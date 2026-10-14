# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import re
from typing import Dict

def parse_duration(duration_str: str) -> int:
    """
    Parse a human‑readable duration string and return the total number of seconds.

    Supported units (case‑insensitive):
        - days: d, day, days
        - hours: h, hr, hrs, hour, hours
        - minutes: m, min, mins, minute, minutes
        - seconds: s, sec, secs, second, seconds

    Numbers may be integers or floats. Units may be separated by spaces,
    commas or appear directly adjacent (e.g., "1h30m").

    Raises:
        ValueError: If the string cannot be parsed or contains unknown units.
    """
    if not isinstance(duration_str, str):
        raise TypeError("duration_str must be a string")

    # Normalise the string
    s = duration_str.lower().strip()
    if not s:
        raise ValueError("Empty duration string")

    # Mapping of unit aliases to their multiplier in seconds
    unit_map: Dict[str, int] = {
        "d": 86400, "day": 86400, "days": 86400,
        "h": 3600, "hr": 3600, "hrs": 3600, "hour": 3600, "hours": 3600,
        "m": 60, "min": 60, "mins": 60, "minute": 60, "minutes": 60,
        "s": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1,
    }

    # Regex to find all number‑unit pairs
    pattern = re.compile(
        r"(?P<value>\d+(?:\.\d*)?)\s*(?P<unit>d|day|days|h|hr|hrs|hour|hours|"
        r"m|min|mins|minute|minutes|s|sec|secs|second|seconds)\b"
    )
    total_seconds = 0.0
    matches = list(pattern.finditer(s))
    if not matches:
        raise ValueError(f"Could not parse duration string: '{duration_str}'")

    for m in matches:
        value = float(m.group("value"))
        unit = m.group("unit")
        if unit not in unit_map:
            raise ValueError(f"Unknown time unit: '{unit}'")
        total_seconds += value * unit_map[unit]

    return int(total_seconds)


if __name__ == "__main__":
    # Simple test suite; will raise if any test fails
    test_cases = {
        "2h 30m": 2 * 3600 + 30 * 60,
        "1d": 86400,
        "45s": 45,
        "1h30m": 1 * 3600 + 30 * 60,
        "2 days, 3 hours, 4 minutes, 5 seconds": 2 * 86400 + 3 * 3600 + 4 * 60 + 5,
        "0.5h": int(0.5 * 3600),
        "3hrs 15mins": 3 * 3600 + 15 * 60,
        "   10   s  ": 10,
    }

    for inp, expected in test_cases.items():
        result = parse_duration(inp)
        if result != expected:
            raise AssertionError(f"parse_duration('{inp}') returned {result}, expected {expected}")

    # Test invalid inputs
    invalid_inputs = ["", "abc", "5x", "10"]
    for inp in invalid_inputs:
        try:
            parse_duration(inp)
        except ValueError:
            continue
        else:
            raise AssertionError(f"Expected ValueError for input: '{inp}'")
    print("All tests passed.")