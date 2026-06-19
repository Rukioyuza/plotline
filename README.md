<h1 align="left">plotline</h1>

<p align="left">
  <img src="https://img.shields.io/badge/Python-181717?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Output-SVG-181717?style=for-the-badge&logo=svg&logoColor=white" />
  <img src="https://img.shields.io/badge/Dependencies-None-181717?style=for-the-badge" />
</p>

Small charts with no dependencies. Line, bar and scatter charts are written as plain SVG files, and any chart can print a rough text preview in the terminal.

---

### About

- **Three chart types.** `LineChart`, `ScatterChart` and `BarChart`, each with any number of series.
- **Nice ticks.** Axis ticks are spaced by 1, 2 or 5 times a power of ten, so you get `0, 20, 40` instead of `0, 17.3, 34.6`.
- **Labels.** Title, axis labels and a legend (shown automatically when there is more than one series).
- **Plain SVG.** Built with `xml.etree`, so the output is always well-formed and text is escaped.
- **Text preview.** `chart.to_ascii()` draws the chart with characters for a quick look without opening a file.

---

### Install

```sh
git clone https://github.com/Rukioyuza/plotline
cd plotline
pip install .
```

Requires Python 3.10 or newer.

---

### Usage

```python
from plotline import BarChart, LineChart, ScatterChart

chart = LineChart(title="Average temperature", x_label="Month", y_label="°C", markers=True)
months = list(range(1, 13))
chart.add_series("Oslo", months, [-4, -4, 0, 5, 11, 15, 17, 16, 11, 6, 1, -3])
chart.add_series("Lisbon", months, [11, 12, 14, 15, 18, 21, 23, 24, 22, 18, 14, 12])
chart.save("temperature.svg")
print(chart.to_ascii())

bars = BarChart(["Mon", "Tue", "Wed", "Thu", "Fri"], title="Commits per day")
bars.add_series("Week 1", [4, 7, 3, 8, 5])
bars.add_series("Week 2", [6, 2, 9, 4, 7])
bars.save("commits.svg")

dots = ScatterChart(title="Height vs weight", x_label="cm", y_label="kg")
dots.add_series("Class A", [160, 172, 181, 168], [55, 70, 82, 61])
dots.save("scatter.svg")
```

```
Commits per day
Mon |################## 4
    |=========================== 6
Tue |############################### 7
    |========= 2
...
# Week 1  = Week 2
```

`examples/make_charts.py` writes a line, bar and scatter chart into `examples/output/`:

```sh
python examples/make_charts.py
```

---

### Chart options

| Option | Default | Purpose |
| --- | --- | --- |
| `title` | `""` | Text above the chart |
| `x_label` / `y_label` | `""` | Axis titles |
| `width` / `height` | `640` / `400` | Size in pixels |
| `legend` | `None` | `None` shows a legend only for more than one series, `True` / `False` force it |
| `markers` | `False` | `LineChart` only: draw a dot on every point |

| Method | Purpose |
| --- | --- |
| `add_series(name, x, y, color=None)` | Line and scatter charts. `x` and `y` must be the same length |
| `add_series(name, values, color=None)` | Bar charts. One value per category |
| `to_svg()` | The chart as an SVG string |
| `save(path)` | Write the SVG to a file and return the `Path` |
| `to_ascii(width, height)` | Text preview for the terminal |
| `x_ticks()` / `y_ticks()` | The tick values the axes will use |

Colours come from the Tableau 10 palette in order. Pass `color="#123456"` to pick your own.

The tick helpers are public too: `nice_ticks(low, high, max_ticks=6)`, `nice_number(value, round_result)` and `format_tick(value, step)`.

---

### Running the tests

```sh
pip install -e .
python -m unittest discover -s tests
```

The tests check tick generation and scaling, and parse every rendered SVG with `xml.etree` to check it contains the expected elements.

---

### License

MIT
