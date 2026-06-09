"""Rough text previews of charts for the terminal."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import pairwise

__all__ = ["bars_to_ascii", "xy_to_ascii"]

MARKERS = "*o+x@%"
FILLS = "#=%@+-"

XYData = tuple[str, Sequence[float], Sequence[float]]


def _short(value: float) -> str:
    return f"{value:.4g}"


def _bounds(values: list[float]) -> tuple[float, float]:
    low, high = min(values), max(values)
    if low == high:
        low, high = low - 1, high + 1
    return low, high


def xy_to_ascii(
    series: Sequence[XYData],
    width: int = 60,
    height: int = 15,
    connect: bool = True,
    title: str = "",
) -> str:
    """Draw x/y series on a character grid.

    Each series gets its own marker. With connect, points are joined by
    straight runs of the same marker.
    """
    if width < 2 or height < 2:
        raise ValueError("width and height must be at least 2")
    xs = [x for _, sx, _ in series for x in sx]
    ys = [y for _, _, sy in series for y in sy]
    x_low, x_high = _bounds(xs)
    y_low, y_high = _bounds(ys)

    def cell(x: float, y: float) -> tuple[int, int]:
        col = round((x - x_low) / (x_high - x_low) * (width - 1))
        row = height - 1 - round((y - y_low) / (y_high - y_low) * (height - 1))
        return col, row

    grid = [[" "] * width for _ in range(height)]
    for index, (_, sx, sy) in enumerate(series):
        mark = MARKERS[index % len(MARKERS)]
        points = [cell(x, y) for x, y in zip(sx, sy, strict=True)]
        if connect:
            for (c0, r0), (c1, r1) in pairwise(points):
                steps = max(abs(c1 - c0), abs(r1 - r0), 1)
                for s in range(steps + 1):
                    col = round(c0 + (c1 - c0) * s / steps)
                    row = round(r0 + (r1 - r0) * s / steps)
                    grid[row][col] = mark
        for col, row in points:
            grid[row][col] = mark

    top, bottom = _short(y_high), _short(y_low)
    label_width = max(len(top), len(bottom))
    lines = [title] if title else []
    for row_index, cells in enumerate(grid):
        label = top if row_index == 0 else bottom if row_index == height - 1 else ""
        lines.append(f"{label:>{label_width}} |{''.join(cells)}".rstrip())
    lines.append(" " * label_width + " +" + "-" * width)
    left, right = _short(x_low), _short(x_high)
    gap = max(1, width - len(left) - len(right))
    lines.append(" " * (label_width + 2) + left + " " * gap + right)
    if len(series) > 1:
        legend = "  ".join(
            f"{MARKERS[i % len(MARKERS)]} {name}"
            for i, (name, _, _) in enumerate(series)
        )
        lines.append(legend)
    return "\n".join(lines)


def bars_to_ascii(
    categories: Sequence[str],
    series: Sequence[tuple[str, Sequence[float]]],
    width: int = 40,
    title: str = "",
) -> str:
    """Draw grouped values as horizontal bars, one row per value."""
    if width < 1:
        raise ValueError("width must be at least 1")
    biggest = max((abs(v) for _, values in series for v in values), default=0.0)
    biggest = biggest or 1.0
    label_width = max(len(c) for c in categories)
    lines = [title] if title else []
    for i, category in enumerate(categories):
        for j, (_, values) in enumerate(series):
            value = values[i]
            bar = FILLS[j % len(FILLS)] * round(abs(value) / biggest * width)
            label = category if j == 0 else ""
            lines.append(f"{label:<{label_width}} |{bar} {_short(value)}")
    if len(series) > 1:
        lines.append(
            "  ".join(
                f"{FILLS[j % len(FILLS)]} {name}" for j, (name, _) in enumerate(series)
            )
        )
    return "\n".join(lines)
