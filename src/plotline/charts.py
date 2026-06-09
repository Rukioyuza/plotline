"""Line, scatter and bar charts rendered to SVG."""

from __future__ import annotations

import math
import os
import xml.etree.ElementTree as ET
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .ascii import bars_to_ascii, xy_to_ascii
from .scale import BandScale, LinearScale
from .ticks import format_tick, nice_ticks, tick_step

__all__ = ["BarChart", "Chart", "LineChart", "ScatterChart", "Series"]

SVG_NS = "http://www.w3.org/2000/svg"

# Tableau 10 colours: distinct from each other and readable on white.
PALETTE = (
    "#4e79a7",
    "#f28e2b",
    "#e15759",
    "#76b7b2",
    "#59a14f",
    "#edc948",
    "#b07aa1",
    "#ff9da7",
    "#9c755f",
    "#bab0ac",
)

AXIS_COLOR = "#333333"
GRID_COLOR = "#e5e5e5"
TEXT_COLOR = "#222222"
CHAR_WIDTH = 7  # rough width of a 12px sans-serif character


@dataclass
class Series:
    """One named set of points (or bar values) and its colour."""

    name: str
    x: list[float]
    y: list[float]
    color: str


@dataclass(frozen=True)
class Box:
    """The plot area in pixels."""

    left: float
    top: float
    right: float
    bottom: float


def _fmt(value: float) -> str:
    """Format a coordinate with at most two decimals."""
    text = f"{value:.2f}".rstrip("0").rstrip(".")
    return "0" if text == "-0" else text


def _el(
    parent: ET.Element, tag: str, text: str | None = None, **attrs: str | float
) -> ET.Element:
    """Add a child element. class_ becomes class and font_size font-size."""
    clean = {
        name.rstrip("_").replace("_", "-"): _fmt(v) if isinstance(v, float) else str(v)
        for name, v in attrs.items()
    }
    element = ET.SubElement(parent, tag, clean)
    if text is not None:
        element.text = text
    return element


def _numbers(values: Sequence[float], what: str) -> list[float]:
    result = []
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{what} must be numbers, got {value!r}")
        if not math.isfinite(value):
            raise ValueError(f"{what} must be finite, got {value!r}")
        result.append(float(value))
    return result


class Chart:
    """Shared layout: title, y axis, grid, axis labels and legend.

    Subclasses add series and draw the x axis and the data.
    """

    def __init__(
        self,
        *,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        width: int = 640,
        height: int = 400,
        legend: bool | None = None,
    ) -> None:
        if width < 100 or height < 100:
            raise ValueError("charts must be at least 100x100 pixels")
        self.title = title
        self.x_label = x_label
        self.y_label = y_label
        self.width = width
        self.height = height
        self.legend = legend
        self.series: list[Series] = []

    def _next_color(self) -> str:
        return PALETTE[len(self.series) % len(PALETTE)]

    def _y_values(self) -> list[float]:
        return [y for s in self.series for y in s.y]

    def y_ticks(self) -> list[float]:
        """Tick values for the y axis."""
        values = self._y_values()
        return nice_ticks(min(values), max(values))

    def _show_legend(self) -> bool:
        return self.legend if self.legend is not None else len(self.series) > 1

    def render(self) -> ET.Element:
        """Build the chart as an ElementTree <svg> element."""
        if not self.series:
            raise ValueError("add at least one series before rendering")
        y_ticks = self.y_ticks()
        y_step = tick_step(y_ticks)
        y_tick_labels = [format_tick(t, y_step) for t in y_ticks]

        left = 16 + CHAR_WIDTH * max(len(t) for t in y_tick_labels)
        if self.y_label:
            left += 22
        right = self.width - 20
        if self._show_legend():
            right -= 36 + CHAR_WIDTH * max(len(s.name) for s in self.series)
        top = 48 if self.title else 20
        bottom = self.height - (58 if self.x_label else 36)
        box = Box(left, top, right, bottom)
        y_scale = LinearScale((y_ticks[0], y_ticks[-1]), (box.bottom, box.top))

        svg = ET.Element(
            "svg",
            {
                "xmlns": SVG_NS,
                "width": str(self.width),
                "height": str(self.height),
                "viewBox": f"0 0 {self.width} {self.height}",
                "font-family": "Helvetica, Arial, sans-serif",
                "font-size": "12",
                "fill": TEXT_COLOR,
            },
        )
        _el(svg, "rect", class_="background", width="100%", height="100%", fill="white")
        if self.title:
            _el(
                svg,
                "text",
                self.title,
                class_="title",
                x=self.width / 2,
                y=28.0,
                text_anchor="middle",
                font_size=16,
                font_weight="bold",
            )

        grid = _el(svg, "g", class_="y-axis")
        for tick, label in zip(y_ticks, y_tick_labels, strict=True):
            y = y_scale(tick)
            _el(grid, "line", x1=box.left, x2=box.right, y1=y, y2=y, stroke=GRID_COLOR)
            _el(
                grid,
                "text",
                label,
                x=box.left - 8,
                y=y,
                text_anchor="end",
                dominant_baseline="middle",
            )
        _el(
            grid,
            "line",
            x1=box.left,
            x2=box.left,
            y1=box.top,
            y2=box.bottom,
            stroke=AXIS_COLOR,
        )

        self._draw_plot(svg, box, y_scale)

        if self.x_label:
            _el(
                svg,
                "text",
                self.x_label,
                class_="x-label",
                x=(box.left + box.right) / 2,
                y=self.height - 12.0,
                text_anchor="middle",
            )
        if self.y_label:
            cx, cy = 16.0, (box.top + box.bottom) / 2
            _el(
                svg,
                "text",
                self.y_label,
                class_="y-label",
                x=cx,
                y=cy,
                text_anchor="middle",
                transform=f"rotate(-90 {_fmt(cx)} {_fmt(cy)})",
            )
        if self._show_legend():
            self._draw_legend(svg, box)
        return svg

    def _draw_plot(self, svg: ET.Element, box: Box, y_scale: LinearScale) -> None:
        raise NotImplementedError

    def _draw_legend(self, svg: ET.Element, box: Box) -> None:
        legend = _el(svg, "g", class_="legend")
        x = box.right + 20
        for i, series in enumerate(self.series):
            y = box.top + i * 20
            item = _el(legend, "g", class_="legend-item")
            _el(item, "rect", x=x, y=y, width=12, height=12, fill=series.color)
            _el(
                item, "text", series.name, x=x + 18, y=y + 6, dominant_baseline="middle"
            )

    def to_svg(self) -> str:
        """Return the chart as an SVG document string."""
        svg = self.render()
        ET.indent(svg)
        body = ET.tostring(svg, encoding="unicode")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n"

    def save(self, path: str | os.PathLike[str]) -> Path:
        """Write the chart to an .svg file and return its path."""
        target = Path(path)
        target.write_text(self.to_svg(), encoding="utf-8")
        return target

    def to_ascii(self, width: int = 60, height: int = 15) -> str:
        """A rough text preview for the terminal."""
        raise NotImplementedError


class _XYChart(Chart):
    """Base for charts with numeric x and y values."""

    def add_series(
        self,
        name: str,
        x: Sequence[float],
        y: Sequence[float],
        color: str | None = None,
    ) -> Series:
        """Add a series of (x, y) points and return it."""
        xs, ys = _numbers(x, "x values"), _numbers(y, "y values")
        if len(xs) != len(ys):
            raise ValueError(f"x has {len(xs)} values but y has {len(ys)}")
        if not xs:
            raise ValueError("a series needs at least one point")
        series = Series(name, xs, ys, color or self._next_color())
        self.series.append(series)
        return series

    def x_ticks(self) -> list[float]:
        """Tick values for the x axis."""
        values = [x for s in self.series for x in s.x]
        return nice_ticks(min(values), max(values))

    def _draw_plot(self, svg: ET.Element, box: Box, y_scale: LinearScale) -> None:
        ticks = self.x_ticks()
        step = tick_step(ticks)
        x_scale = LinearScale((ticks[0], ticks[-1]), (box.left, box.right))
        axis = _el(svg, "g", class_="x-axis")
        for tick in ticks:
            x = x_scale(tick)
            _el(axis, "line", x1=x, x2=x, y1=box.top, y2=box.bottom, stroke=GRID_COLOR)
            _el(
                axis,
                "text",
                format_tick(tick, step),
                x=x,
                y=box.bottom + 18,
                text_anchor="middle",
            )
        _el(
            axis,
            "line",
            x1=box.left,
            x2=box.right,
            y1=box.bottom,
            y2=box.bottom,
            stroke=AXIS_COLOR,
        )
        for series in self.series:
            group = _el(svg, "g", class_="series", data_name=series.name)
            points = [
                (x_scale(x), y_scale(y))
                for x, y in zip(series.x, series.y, strict=True)
            ]
            self._draw_series(group, series, points)

    def _draw_series(
        self, group: ET.Element, series: Series, points: list[tuple[float, float]]
    ) -> None:
        raise NotImplementedError


class LineChart(_XYChart):
    """Connects each series' points with a line, in the order given."""

    def __init__(
        self,
        *,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        width: int = 640,
        height: int = 400,
        legend: bool | None = None,
        markers: bool = False,
    ) -> None:
        super().__init__(
            title=title,
            x_label=x_label,
            y_label=y_label,
            width=width,
            height=height,
            legend=legend,
        )
        self.markers = markers

    def _draw_series(
        self, group: ET.Element, series: Series, points: list[tuple[float, float]]
    ) -> None:
        _el(
            group,
            "polyline",
            points=" ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in points),
            fill="none",
            stroke=series.color,
            stroke_width=2,
            stroke_linejoin="round",
            stroke_linecap="round",
        )
        if self.markers:
            for x, y in points:
                _el(group, "circle", cx=x, cy=y, r=3, fill=series.color)

    def to_ascii(self, width: int = 60, height: int = 15) -> str:
        data = [(s.name, s.x, s.y) for s in self.series]
        return xy_to_ascii(data, width, height, connect=True, title=self.title)


class ScatterChart(_XYChart):
    """Draws each point as a dot."""

    radius = 4

    def _draw_series(
        self, group: ET.Element, series: Series, points: list[tuple[float, float]]
    ) -> None:
        for x, y in points:
            _el(
                group,
                "circle",
                cx=x,
                cy=y,
                r=self.radius,
                fill=series.color,
                fill_opacity="0.8",
            )

    def to_ascii(self, width: int = 60, height: int = 15) -> str:
        data = [(s.name, s.x, s.y) for s in self.series]
        return xy_to_ascii(data, width, height, connect=False, title=self.title)


class BarChart(Chart):
    """Vertical bars, grouped by category when there are several series."""

    def __init__(
        self,
        categories: Sequence[str],
        *,
        title: str = "",
        x_label: str = "",
        y_label: str = "",
        width: int = 640,
        height: int = 400,
        legend: bool | None = None,
    ) -> None:
        super().__init__(
            title=title,
            x_label=x_label,
            y_label=y_label,
            width=width,
            height=height,
            legend=legend,
        )
        if not categories:
            raise ValueError("a bar chart needs at least one category")
        self.categories = [str(c) for c in categories]

    def add_series(
        self, name: str, values: Sequence[float], color: str | None = None
    ) -> Series:
        """Add one value per category and return the series."""
        ys = _numbers(values, "values")
        if len(ys) != len(self.categories):
            raise ValueError(
                f"expected {len(self.categories)} values (one per category), "
                f"got {len(ys)}"
            )
        xs = [float(i) for i in range(len(ys))]
        series = Series(name, xs, ys, color or self._next_color())
        self.series.append(series)
        return series

    def y_ticks(self) -> list[float]:
        # Bars grow from zero, so zero must be on the axis.
        values = self._y_values()
        return nice_ticks(min(0.0, *values), max(0.0, *values))

    def _draw_plot(self, svg: ET.Element, box: Box, y_scale: LinearScale) -> None:
        bands = BandScale(self.categories, (box.left, box.right))
        axis = _el(svg, "g", class_="x-axis")
        for i, category in enumerate(self.categories):
            _el(
                axis,
                "text",
                category,
                x=bands.center(i),
                y=box.bottom + 18,
                text_anchor="middle",
            )

        zero = y_scale(0.0)
        bar_width = bands.bandwidth / len(self.series)
        for j, series in enumerate(self.series):
            group = _el(svg, "g", class_="series", data_name=series.name)
            for i, value in enumerate(series.y):
                top = min(zero, y_scale(value))
                _el(
                    group,
                    "rect",
                    class_="bar",
                    x=bands.start(i) + j * bar_width,
                    y=top,
                    width=bar_width,
                    height=abs(y_scale(value) - zero),
                    fill=series.color,
                )
        _el(
            axis, "line", x1=box.left, x2=box.right, y1=zero, y2=zero, stroke=AXIS_COLOR
        )

    def to_ascii(self, width: int = 40, height: int = 0) -> str:
        """Horizontal text bars. height is ignored; rows follow the data."""
        data = [(s.name, s.y) for s in self.series]
        return bars_to_ascii(self.categories, data, width, title=self.title)
