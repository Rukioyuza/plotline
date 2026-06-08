"""Choosing "nice" tick values for an axis.

Uses the classic approach from Paul Heckbert's "Nice Numbers for Graph
Labels" (Graphics Gems, 1990): ticks are spaced by 1, 2 or 5 times a
power of ten, and the axis is widened to start and end on a tick.
"""

from __future__ import annotations

import math

__all__ = ["format_tick", "nice_number", "nice_ticks", "tick_step"]


def nice_number(value: float, round_result: bool) -> float:
    """Return a 1, 2, 5 or 10 times a power of ten close to value.

    With round_result the closest nice number is returned, otherwise the
    smallest nice number that is greater than or equal to value.
    """
    if value <= 0:
        raise ValueError("value must be positive")
    exponent = math.floor(math.log10(value))
    fraction = value / 10**exponent
    if round_result:
        if fraction < 1.5:
            nice = 1.0
        elif fraction < 3:
            nice = 2.0
        elif fraction < 7:
            nice = 5.0
        else:
            nice = 10.0
    else:
        if fraction <= 1:
            nice = 1.0
        elif fraction <= 2:
            nice = 2.0
        elif fraction <= 5:
            nice = 5.0
        else:
            nice = 10.0
    return nice * 10.0**exponent


def _decimals(step: float) -> int:
    """How many decimal places are needed to print multiples of step."""
    return max(0, -math.floor(math.log10(step) + 1e-9))


def nice_ticks(low: float, high: float, max_ticks: int = 6) -> list[float]:
    """Return evenly spaced, round tick values covering [low, high].

    The first tick is <= low and the last tick is >= high. At most about
    max_ticks + 1 values are returned.
    """
    if max_ticks < 2:
        raise ValueError("max_ticks must be at least 2")
    if not (math.isfinite(low) and math.isfinite(high)):
        raise ValueError("tick range must be finite")
    if low > high:
        low, high = high, low
    if low == high:
        # A flat range still needs an axis: pad it by 10% (or 1 around zero).
        pad = abs(low) * 0.1 if low else 1.0
        low, high = low - pad, high + pad

    span = nice_number(high - low, round_result=False)
    step = nice_number(span / (max_ticks - 1), round_result=True)
    first = math.floor(low / step + 1e-9) * step
    last = math.ceil(high / step - 1e-9) * step
    count = round((last - first) / step) + 1
    decimals = _decimals(step)
    ticks = []
    for i in range(count):
        tick = round(first + i * step, decimals)
        ticks.append(0.0 if tick == 0 else tick)
    return ticks


def tick_step(ticks: list[float]) -> float:
    """The spacing between ticks (1.0 if there is only one)."""
    return ticks[1] - ticks[0] if len(ticks) > 1 else 1.0


def format_tick(value: float, step: float) -> str:
    """Format a tick value with just enough decimal places for its step."""
    decimals = _decimals(abs(step)) if step else 0
    text = f"{value:,.{decimals}f}"
    if text.startswith("-") and float(text.replace(",", "")) == 0:
        text = text[1:]
    return text
