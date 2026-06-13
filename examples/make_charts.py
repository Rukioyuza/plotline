"""Write a few example charts to SVG and print text previews.

Run from the repo root after `pip install -e .`:

    python examples/make_charts.py            # writes into examples/output/
    python examples/make_charts.py some/dir   # or into a folder of your choice
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

from plotline import BarChart, LineChart, ScatterChart


def line_example() -> LineChart:
    chart = LineChart(
        title="Average temperature",
        x_label="Month",
        y_label="°C",
        markers=True,
    )
    months = list(range(1, 13))
    chart.add_series("Oslo", months, [-4, -4, 0, 5, 11, 15, 17, 16, 11, 6, 1, -3])
    chart.add_series("Lisbon", months, [11, 12, 14, 15, 18, 21, 23, 24, 22, 18, 14, 12])
    return chart


def bar_example() -> BarChart:
    chart = BarChart(
        ["Mon", "Tue", "Wed", "Thu", "Fri"],
        title="Commits per day",
        y_label="Commits",
    )
    chart.add_series("Week 1", [4, 7, 3, 8, 5])
    chart.add_series("Week 2", [6, 2, 9, 4, 7])
    return chart


def scatter_example() -> ScatterChart:
    chart = ScatterChart(title="sin(x) with a phase shift", x_label="x", y_label="y")
    xs = [i / 4 for i in range(41)]
    chart.add_series("sin(x)", xs, [math.sin(x) for x in xs])
    chart.add_series("sin(x + 1)", xs, [math.sin(x + 1) for x in xs])
    return chart


def main() -> None:
    default = Path(__file__).resolve().parent / "output"
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else default
    out_dir.mkdir(parents=True, exist_ok=True)

    charts = {
        "line.svg": line_example(),
        "bars.svg": bar_example(),
        "scatter.svg": scatter_example(),
    }
    for filename, chart in charts.items():
        path = chart.save(out_dir / filename)
        print(f"wrote {path}")
        print(chart.to_ascii())
        print()


if __name__ == "__main__":
    main()
