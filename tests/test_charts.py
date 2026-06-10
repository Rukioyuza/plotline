import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from plotline import PALETTE, BarChart, LineChart, ScatterChart

NS = {"svg": "http://www.w3.org/2000/svg"}


def parse(svg_text: str) -> ET.Element:
    """Parse an SVG string; fails the test if it is not well-formed XML."""
    return ET.fromstring(svg_text.encode("utf-8"))


def texts(root: ET.Element) -> list[str]:
    return [t.text or "" for t in root.iter("{http://www.w3.org/2000/svg}text")]


def groups(root: ET.Element, cls: str) -> list[ET.Element]:
    return [g for g in root.findall(".//svg:g", NS) if g.get("class") == cls]


class LineChartTests(unittest.TestCase):
    def make(self) -> LineChart:
        chart = LineChart(title="Sales", x_label="Month", y_label="Units")
        chart.add_series("2023", [1, 2, 3, 4], [10, 25, 18, 30])
        chart.add_series("2024", [1, 2, 3, 4], [12, 20, 26, 41])
        return chart

    def test_is_well_formed_svg(self) -> None:
        root = parse(self.make().to_svg())
        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertEqual(root.get("width"), "640")
        self.assertEqual(root.get("viewBox"), "0 0 640 400")

    def test_title_labels_and_ticks(self) -> None:
        all_text = texts(parse(self.make().to_svg()))
        for expected in ["Sales", "Month", "Units", "10", "50", "1", "4"]:
            self.assertIn(expected, all_text)

    def test_one_polyline_per_series(self) -> None:
        root = parse(self.make().to_svg())
        series = groups(root, "series")
        self.assertEqual([g.get("data-name") for g in series], ["2023", "2024"])
        for group in series:
            polylines = group.findall("svg:polyline", NS)
            self.assertEqual(len(polylines), 1)
            self.assertEqual(len(polylines[0].get("points", "").split()), 4)
        colors = [g.find("svg:polyline", NS).get("stroke") for g in series]
        self.assertEqual(colors, list(PALETTE[:2]))

    def test_points_are_scaled_into_the_plot_area(self) -> None:
        chart = LineChart(width=400, height=300)
        chart.add_series("only", [0, 10], [0, 10])
        root = parse(chart.to_svg())
        points = root.find(".//svg:polyline", NS).get("points").split()
        (x0, y0), (x1, y1) = [tuple(map(float, p.split(","))) for p in points]
        self.assertLess(x0, x1)
        self.assertGreater(y0, y1, "bigger values should be drawn higher up")
        for x, y in [(x0, y0), (x1, y1)]:
            self.assertTrue(0 < x < 400 and 0 < y < 300)

    def test_markers(self) -> None:
        chart = LineChart(markers=True)
        chart.add_series("a", [1, 2, 3], [3, 1, 2])
        root = parse(chart.to_svg())
        self.assertEqual(len(root.findall(".//svg:circle", NS)), 3)

    def test_legend(self) -> None:
        root = parse(self.make().to_svg())
        legend = groups(root, "legend")
        self.assertEqual(len(legend), 1)
        self.assertEqual(texts(legend[0]), ["2023", "2024"])

    def test_legend_hidden_for_single_series_unless_asked(self) -> None:
        chart = LineChart()
        chart.add_series("a", [1, 2], [1, 2])
        self.assertEqual(groups(parse(chart.to_svg()), "legend"), [])
        chart.legend = True
        self.assertEqual(len(groups(parse(chart.to_svg()), "legend")), 1)

    def test_special_characters_are_escaped(self) -> None:
        chart = LineChart(title='Profit & "loss" <2024>')
        chart.add_series("<a & b>", [1, 2], [1, 2])
        svg = chart.to_svg()
        self.assertIn("&amp;", svg)
        self.assertIn('Profit & "loss" <2024>', texts(parse(svg)))

    def test_custom_color(self) -> None:
        chart = LineChart()
        chart.add_series("a", [1, 2], [1, 2], color="#123456")
        root = parse(chart.to_svg())
        self.assertEqual(root.find(".//svg:polyline", NS).get("stroke"), "#123456")


class ScatterChartTests(unittest.TestCase):
    def test_one_circle_per_point(self) -> None:
        chart = ScatterChart(title="Scatter")
        chart.add_series("a", [1, 2, 3], [4, 5, 6])
        chart.add_series("b", [1.5, 2.5], [3, 2])
        root = parse(chart.to_svg())
        counts = [len(g.findall("svg:circle", NS)) for g in groups(root, "series")]
        self.assertEqual(counts, [3, 2])
        self.assertIsNone(root.find(".//svg:polyline", NS))


class BarChartTests(unittest.TestCase):
    def test_one_rect_per_value(self) -> None:
        chart = BarChart(["Q1", "Q2", "Q3"], title="Revenue")
        chart.add_series("2023", [5, 8, 6])
        chart.add_series("2024", [7, 9, 11])
        root = parse(chart.to_svg())
        bars = [
            r
            for r in root.iter("{http://www.w3.org/2000/svg}rect")
            if r.get("class") == "bar"
        ]
        self.assertEqual(len(bars), 6)
        for name in ["Q1", "Q2", "Q3"]:
            self.assertIn(name, texts(root))

    def test_axis_starts_at_zero(self) -> None:
        chart = BarChart(["a", "b"])
        chart.add_series("s", [50, 70])
        self.assertEqual(chart.y_ticks()[0], 0)

    def test_negative_values_hang_below_zero(self) -> None:
        chart = BarChart(["up", "down"])
        chart.add_series("s", [10, -10])
        root = parse(chart.to_svg())
        up, down = [
            r
            for r in root.iter("{http://www.w3.org/2000/svg}rect")
            if r.get("class") == "bar"
        ]
        self.assertEqual(float(up.get("height")), float(down.get("height")))
        up_bottom = float(up.get("y")) + float(up.get("height"))
        self.assertAlmostEqual(up_bottom, float(down.get("y")))

    def test_value_count_must_match_categories(self) -> None:
        chart = BarChart(["a", "b"])
        with self.assertRaises(ValueError):
            chart.add_series("s", [1, 2, 3])


class ValidationTests(unittest.TestCase):
    def test_empty_chart_cannot_render(self) -> None:
        with self.assertRaises(ValueError):
            LineChart().to_svg()

    def test_bad_values(self) -> None:
        chart = LineChart()
        with self.assertRaises(ValueError):
            chart.add_series("a", [1, 2], [1])
        with self.assertRaises(ValueError):
            chart.add_series("a", [], [])
        with self.assertRaises(ValueError):
            chart.add_series("a", [1], [float("nan")])
        with self.assertRaises(TypeError):
            chart.add_series("a", [1], ["3"])  # type: ignore[list-item]

    def test_too_small(self) -> None:
        with self.assertRaises(ValueError):
            LineChart(width=50)


class SaveTests(unittest.TestCase):
    def test_save_writes_svg_file(self) -> None:
        chart = BarChart(["a"])
        chart.add_series("s", [1])
        with tempfile.TemporaryDirectory() as folder:
            path = chart.save(Path(folder) / "chart.svg")
            content = path.read_text(encoding="utf-8")
        self.assertTrue(content.startswith('<?xml version="1.0" encoding="UTF-8"?>'))
        parse(content)


class AsciiTests(unittest.TestCase):
    def test_line_preview(self) -> None:
        chart = LineChart(title="Up")
        chart.add_series("a", [0, 10], [0, 10])
        lines = chart.to_ascii(width=20, height=5).splitlines()
        self.assertEqual(lines[0], "Up")
        self.assertTrue(lines[1].startswith("10 |") and lines[1].endswith("*"))
        self.assertTrue(lines[5].startswith(" 0 |*"))
        self.assertEqual(len(lines[1]), len("10 |") + 20)
        self.assertEqual(lines[6], "   +" + "-" * 20)
        self.assertEqual(lines[7].split(), ["0", "10"])
        # every row of the diagonal has a marker
        self.assertTrue(all("*" in line for line in lines[1:6]))

    def test_scatter_preview_has_legend(self) -> None:
        chart = ScatterChart()
        chart.add_series("a", [0, 1], [0, 1])
        chart.add_series("b", [0.5], [0.5])
        text = chart.to_ascii(width=11, height=3)
        self.assertIn("* a  o b", text)
        self.assertEqual(text.count("*") - 1, 2)  # legend adds one
        self.assertEqual(text.count("o") - 1, 1)

    def test_bar_preview(self) -> None:
        chart = BarChart(["cats", "dogs"])
        chart.add_series("votes", [5, 10])
        self.assertEqual(
            chart.to_ascii(width=10).splitlines(),
            ["cats |##### 5", "dogs |########## 10"],
        )


if __name__ == "__main__":
    unittest.main()
