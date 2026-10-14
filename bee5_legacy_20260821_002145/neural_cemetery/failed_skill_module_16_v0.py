# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import re

def parse_duration(duration_str: str) -> int:
    """
    Parse a human‑readable duration string into total seconds.

    Supported units (case‑insensitive):
        d - days
        h - hours
        m - minutes
        s - seconds

    The input may contain multiple components, e.g. "2d 3h15m 30s" or "1h30m".
    Whitespace between components is optional. If a component lacks a unit,
    it is interpreted as seconds.

    Args:
        duration_str: The duration string to parse.

    Returns:
        Total duration in seconds.

    Raises:
        ValueError: If the string cannot be parsed.
    """
    if not isinstance(duration_str, str):
        raise ValueError("Input must be a string")

    pattern = re.compile(r'(?P<value>\d+(?:\.\d+)?)(?P<unit>[dhms]?)', re.IGNORECASE)
    total_seconds = 0.0
    pos = 0
    duration_str = duration_str.strip()
    while pos < len(duration_str):
        match = pattern.match(duration_str, pos)
        if not match:
            raise ValueError(f"Unable to parse at position {pos}: '{duration_str[pos:]}'")
        value = float(match.group('value'))
        unit = match.group('unit').lower()
        if unit == '' or unit == 's':
            factor = 1
        elif unit == 'm':
            factor = 60
        elif unit == 'h':
            factor = 3600
        elif unit == 'd':
            factor = 86400
        else:
            raise ValueError(f"Unknown unit '{unit}'")
        total_seconds += value * factor
        pos = match.end()
        # Skip any whitespace between components
        while pos < len(duration_str) and duration_str[pos].isspace():
            pos += 1

    return int(total_seconds)


if __name__ == "__main__":
    # Basic sanity checks
    assert parse_duration("10") == 10
    assert parse_duration("10s") == 10
    assert parse_duration("2m") == 120
    assert parse_duration("1h") == 3600
    assert parse_duration("1d") == 86400
    assert parse_duration("1h30m") == 5400
    assert parse_duration("2d 3h 4m 5s") == 2*86400 + 3*3600 + 4*60 + 5
    assert parse_duration("  5m   30s ") == 5*60 + 30
    # Fractional values
    assert parse_duration("1.5h") == int(1.5 * 3600)
    assert parse_duration("0.5d") == int(0.5 * 86400)

    # Invalid inputs should raise ValueError
    try:
        parse_duration("abc")
        raise AssertionError("Expected ValueError for 'abc'")
    except ValueError:
        pass

    try:
        parse_duration("10x")
        raise AssertionError("Expected ValueError for unknown unit")
    except ValueError:
        pass

    print("All tests passed.")