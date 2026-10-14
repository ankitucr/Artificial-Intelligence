"""Parse and format human‑readable duration strings using only the Python standard library."""

import re
from typing import Dict, Tuple

SAMPLE_ARGS = {
    "duration": "1d 2h 3m 4s"
}

_UNIT_SECONDS = {
    "d": 86400,  # days
    "h": 3600,   # hours
    "m": 60,     # minutes
    "s": 1       # seconds
}


def parse_duration(duration: str) -> int:
    """Convert a duration string like ``'1d 2h 3m 4s'`` to total seconds.

    Supported units (case‑insensitive):
        d – days
        h – hours
        m – minutes
        s – seconds

    Whitespace between parts is optional. Units may appear in any order.
    """
    if not isinstance(duration, str):
        raise TypeError("duration must be a string")
    total = 0
    pattern = re.compile(r"(?P<value>\d+)\s*(?P<unit>[dhmsDHMS])")
    for match in pattern.finditer(duration):
        value = int(match.group("value"))
        unit = match.group("unit").lower()
        if unit not in _UNIT_SECONDS:
            raise ValueError(f"Unsupported time unit: {unit}")
        total += value * _UNIT_SECONDS[unit]
    if total == 0:
        # If no matches were found, treat as invalid input
        raise ValueError(f"Could not parse duration string: '{duration}'")
    return total


def format_duration(seconds: int) -> str:
    """Format a non‑negative number of seconds as a human‑readable string.

    The output uses the largest possible units (days, hours, minutes, seconds)
    and omits any unit with a zero value, unless the total duration is zero,
    in which case ``'0s'`` is returned.
    """
    if not isinstance(seconds, int):
        raise TypeError("seconds must be an integer")
    if seconds < 0:
        raise ValueError("seconds cannot be negative")
    parts = []
    remainder = seconds
    for unit, unit_sec in (("d", 86400), ("h", 3600), ("m", 60), ("s", 1)):
        if remainder >= unit_sec:
            qty, remainder = divmod(remainder, unit_sec)
            parts.append(f"{qty}{unit}")
    if not parts:
        return "0s"
    return " ".join(parts)


def run(args: Dict) -> Dict:
    """Entry point for the skill.

    Expects a dictionary with key ``duration`` (a string). Returns a dictionary
    containing the computed ``seconds`` and a ``formatted`` version of that
    total duration.
    """
    duration_str = args.get("duration", "")
    seconds = parse_duration(duration_str)
    formatted = format_duration(seconds)
    return {
        "input": duration_str,
        "seconds": seconds,
        "formatted": formatted
    }


if __name__ == "__main__":
    result = run(SAMPLE_ARGS)
    expected_seconds = 1 * 86400 + 2 * 3600 + 3 * 60 + 4
    expected_formatted = "1d 2h 3m 4s"
    if result.get("seconds") != expected_seconds:
        raise AssertionError(
            f"Expected {expected_seconds} seconds, got {result.get('seconds')}"
        )
    if result.get("formatted") != expected_formatted:
        raise AssertionError(
            f"Expected formatted '{expected_formatted}', got '{result.get('formatted')}'"
        )
    print("Duration parsing and formatting test passed.")