# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def parse_duration(duration_str: str) -> int:
    """
    Parse a human‑readable duration string into total seconds.

    Supported units (case‑insensitive):
        weeks: w, week, weeks
        days: d, day, days
        hours: h, hour, hours
        minutes: m, min, mins, minute, minutes
        seconds: s, sec, secs, second, seconds

    Numbers may be integer or float. Units may be separated by spaces or not.
    Examples:
        "1h 30m" -> 5400
        "2h30m"  -> 9000
        "1.5 days" -> 129600
        "3 weeks 4d 5h 6m 7s" -> 1901467

    Raises:
        ValueError: if the string contains an unknown unit or no numbers.
    """
    import re

    # Normalise string
    s = duration_str.lower().strip()
    if not s:
        raise ValueError("Empty duration string")

    # Regex to find number+unit groups
    pattern = re.compile(r'(?P<value>\d+(?:\.\d*)?)\s*(?P<unit>w|weeks?|d|days?|h|hours?|m|mins?|minutes?|s|secs?|seconds?)')
    matches = pattern.finditer(s)

    total_seconds = 0.0
    found = False
    unit_factors = {
        'w': 7 * 24 * 3600,
        'week': 7 * 24 * 3600,
        'weeks': 7 * 24 * 3600,
        'd': 24 * 3600,
        'day': 24 * 3600,
        'days': 24 * 3600,
        'h': 3600,
        'hour': 3600,
        'hours': 3600,
        'm': 60,
        'min': 60,
        'mins': 60,
        'minute': 60,
        'minutes': 60,
        's': 1,
        'sec': 1,
        'secs': 1,
        'second': 1,
        'seconds': 1,
    }

    for m in matches:
        found = True
        value = float(m.group('value'))
        unit = m.group('unit')
        factor = unit_factors.get(unit)
        if factor is None:
            raise ValueError(f"Unknown time unit: {unit}")
        total_seconds += value * factor

    if not found:
        raise ValueError(f"No valid time components found in '{duration_str}'")
    return int(total_seconds)


if __name__ == "__main__":
    # Simple test suite
    test_cases = [
        ("1s", 1),
        ("45s", 45),
        ("2m", 120),
        ("3m 30s", 210),
        ("1h", 3600),
        ("1h 15m", 4500),
        ("2h30m", 9000),
        ("1d", 86400),
        ("1d 2h", 93600),
        ("1.5d", 129600),
        ("1w", 604800),
        ("2 weeks 3 days 4h 5m 6s", 2*604800 + 3*86400 + 4*3600 + 5*60 + 6),
        ("0.5h", 1800),
        ("   3   h   5   m  ", 11100),
    ]

    for inp, expected in test_cases:
        result = parse_duration(inp)
        if result != expected:
            raise AssertionError(f"parse_duration({inp!r}) = {result}, expected {expected}")

    # Edge cases
    try:
        parse_duration("")
        raise AssertionError("Empty string should raise ValueError")
    except ValueError:
        pass

    try:
        parse_duration("10x")
        raise AssertionError("Invalid unit should raise ValueError")
    except ValueError:
        pass

    print("All tests passed.")