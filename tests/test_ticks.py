import unittest
from itertools import pairwise

from plotline import LinearScale, nice_number, nice_ticks
from plotline.scale import BandScale
from plotline.ticks import format_tick


class NiceNumberTests(unittest.TestCase):
    def test_rounded(self) -> None:
        cases = {1.2: 1, 2.4: 2, 3.5: 5, 6.9: 5, 7.5: 10, 0.034: 0.05, 1400: 1000}
        for value, expected in cases.items():
            self.assertAlmostEqual(nice_number(value, True), expected, msg=value)

    def test_ceiling(self) -> None:
        cases = {1.0: 1, 1.2: 2, 2.5: 5, 5.1: 10, 0.034: 0.05, 1400: 2000}
        for value, expected in cases.items():
            self.assertAlmostEqual(nice_number(value, False), expected, msg=value)

    def test_rejects_non_positive(self) -> None:
        with self.assertRaises(ValueError):
            nice_number(0, True)


class NiceTicksTests(unittest.TestCase):
    def test_simple_ranges(self) -> None:
        self.assertEqual(nice_ticks(0, 10), [0, 2, 4, 6, 8, 10])
        self.assertEqual(nice_ticks(0, 100), [0, 20, 40, 60, 80, 100])
        self.assertEqual(nice_ticks(0, 1), [0, 0.2, 0.4, 0.6, 0.8, 1.0])

    def test_range_is_widened_to_ticks(self) -> None:
        self.assertEqual(nice_ticks(3, 97), [0, 20, 40, 60, 80, 100])
        self.assertEqual(nice_ticks(-3, 7), [-4, -2, 0, 2, 4, 6, 8])

    def test_no_float_noise(self) -> None:
        self.assertEqual(nice_ticks(0.1, 0.7), [0, 0.2, 0.4, 0.6, 0.8])
        self.assertEqual(nice_ticks(0.1, 0.35), [0.1, 0.2, 0.3, 0.4])
        for tick in nice_ticks(0.001, 0.0042):
            self.assertEqual(tick, round(tick, 6))

    def test_reversed_input(self) -> None:
        self.assertEqual(nice_ticks(10, 0), nice_ticks(0, 10))

    def test_flat_range(self) -> None:
        ticks = nice_ticks(5, 5)
        self.assertLess(ticks[0], 5)
        self.assertGreater(ticks[-1], 5)
        zero = nice_ticks(0, 0)
        self.assertLess(zero[0], 0)
        self.assertGreater(zero[-1], 0)

    def test_properties_hold_for_many_ranges(self) -> None:
        ranges = [(0, 3), (-250, 1234), (0.5, 0.51), (1e6, 3.3e6), (-9, -2), (17, 18)]
        for low, high in ranges:
            with self.subTest(low=low, high=high):
                ticks = nice_ticks(low, high)
                self.assertLessEqual(ticks[0], low)
                self.assertGreaterEqual(ticks[-1], high)
                self.assertTrue(3 <= len(ticks) <= 11, ticks)
                steps = {round(b - a, 9) for a, b in pairwise(ticks)}
                self.assertEqual(len(steps), 1, ticks)

    def test_max_ticks(self) -> None:
        self.assertLessEqual(len(nice_ticks(0, 100, max_ticks=3)), 4)
        with self.assertRaises(ValueError):
            nice_ticks(0, 1, max_ticks=1)
        with self.assertRaises(ValueError):
            nice_ticks(0, float("inf"))


class FormatTickTests(unittest.TestCase):
    def test_decimals_follow_step(self) -> None:
        self.assertEqual(format_tick(4.0, 2.0), "4")
        self.assertEqual(format_tick(0.4, 0.2), "0.4")
        self.assertEqual(format_tick(0.05, 0.05), "0.05")
        self.assertEqual(format_tick(2500000.0, 500000.0), "2,500,000")

    def test_no_negative_zero(self) -> None:
        self.assertEqual(format_tick(-0.0, 1.0), "0")
        self.assertEqual(format_tick(-0.0001, 0.1), "0.0")


class ScaleTests(unittest.TestCase):
    def test_linear(self) -> None:
        scale = LinearScale((0, 10), (0, 100))
        self.assertEqual(scale(0), 0)
        self.assertEqual(scale(2.5), 25)
        self.assertEqual(scale(10), 100)
        self.assertEqual(scale.invert(50), 5)

    def test_inverted_range_for_svg_y(self) -> None:
        scale = LinearScale((0, 100), (400, 0))
        self.assertEqual(scale(0), 400)
        self.assertEqual(scale(100), 0)
        self.assertEqual(scale(25), 300)

    def test_zero_width_domain(self) -> None:
        scale = LinearScale((5, 5), (0, 100))
        self.assertEqual(scale(5), 50)

    def test_band(self) -> None:
        bands = BandScale(["a", "b", "c", "d"], (0, 400), padding=0.5)
        self.assertEqual(bands.step, 100)
        self.assertEqual(bands.bandwidth, 50)
        self.assertEqual(bands.start(0), 25)
        self.assertEqual(bands.center(1), 150)
        with self.assertRaises(ValueError):
            BandScale([], (0, 1))


if __name__ == "__main__":
    unittest.main()
