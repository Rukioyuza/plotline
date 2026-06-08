"""Mapping data values to pixel positions."""

from __future__ import annotations

from collections.abc import Sequence

__all__ = ["BandScale", "LinearScale"]


class LinearScale:
    """Maps a numeric domain onto a pixel range in a straight line.

    The range may run backwards, which is how the y axis works in SVG
    (bigger values are higher up, so they get smaller y coordinates).
    """

    def __init__(
        self, domain: tuple[float, float], output: tuple[float, float]
    ) -> None:
        low, high = domain
        if low == high:
            low, high = low - 1, high + 1
        self.domain = (low, high)
        self.output = output

    def __call__(self, value: float) -> float:
        d0, d1 = self.domain
        r0, r1 = self.output
        return r0 + (value - d0) / (d1 - d0) * (r1 - r0)

    def invert(self, position: float) -> float:
        """Turn a pixel position back into a data value."""
        d0, d1 = self.domain
        r0, r1 = self.output
        return d0 + (position - r0) / (r1 - r0) * (d1 - d0)


class BandScale:
    """Splits a pixel range into equal bands, one per category.

    padding is the fraction of each band left empty as a gap.
    """

    def __init__(
        self,
        categories: Sequence[str],
        output: tuple[float, float],
        padding: float = 0.2,
    ) -> None:
        if not categories:
            raise ValueError("BandScale needs at least one category")
        if not 0 <= padding < 1:
            raise ValueError("padding must be between 0 and 1")
        self.categories = list(categories)
        self.output = output
        self.padding = padding
        self.step = (output[1] - output[0]) / len(self.categories)

    @property
    def bandwidth(self) -> float:
        """Width of the drawn part of each band."""
        return self.step * (1 - self.padding)

    def start(self, index: int) -> float:
        """Left edge of the drawn part of band number index."""
        return self.output[0] + self.step * index + self.step * self.padding / 2

    def center(self, index: int) -> float:
        """Middle of band number index."""
        return self.output[0] + self.step * (index + 0.5)
