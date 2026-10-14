# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def parse_duration(duration_str: str) -> int:
    """
    Parse a human‑readable duration string into total seconds.

    Supported units (case‑insensitive):
        d  – days
        h  – hours
        m  – minutes
        s  – seconds

    The string may contain multiple units in any order, optionally separated by
    whitespace, e.g. "2h30m", "1d 4h", "45 s", "3h 15m 20s".

    Parameters
    ----------
    duration_str: str
        The duration string to parse.

    Returns
    -------
    int
        Total number of seconds represented by the input string.

    Raises
    ------
    ValueError
        If the string contains an unrecognised format.
    """
    import re

    # Normalise string: strip, lower case, remove surrounding spaces
    s = duration_str.strip().lower()
    if not s:
        raise ValueError("Empty duration string")

    # Regex to capture number + optional whitespace + unit
    pattern = re.compile(r"(?P<value>\d+\.?\d*)\s*(?P<unit>[dhms])")
    matches = pattern.finditer(s)

    total_seconds = 0.0
    found = False
    for m in matches:
        found = True
        value = float(m.group("value"))
        unit = m.group("unit")
        if unit == "d":
            total_seconds += value * 86400
        elif unit == "h":
            total_seconds += value * 3600
        elif unit == "m":
            total_seconds += value * 60
        elif unit == "s":
            total_seconds += value
        else:
            # Should never happen due to regex, but keep safety
            raise ValueError(f"Unsupported unit: {unit}")

    if not found:
        raise ValueError(f"Could not parse duration string: '{duration_str}'")

    return int(round(total_seconds))


if __name__ == "__main__":
    # Self‑test cases
    test_cases = {
        "1d": 86400,
        "2h": 7200,
        "30m": 1800,
        "45s": 45,
        "1d 2h 30m 45s": 93785,
        "2h30m": 9000,
        "3h 15m 20s": 11720,
        "0d0h0m0s": 0,
        "  5m  ": 300,
        "1.5h": 5400,   # fractional hours
        "0.5d": 43200,  # fractional days
        "2.25h30m": 9000,  # mixed fractional and whole
    }

    for inp, expected in test_cases.items():
        result = parse_duration(inp)
        if result != expected:
            raise AssertionError(f"parse_duration('{inp}') = {result}, expected {expected}")

    # Additional edge checks
    try:
        parse_duration("")
        raise AssertionError("Empty string should raise ValueError")
    except ValueError:
        pass

    try:
        parse_duration("invalid")
        raise AssertionError("Invalid format should raise ValueError")
    except ValueError:
        pass

    print("All parse_duration tests passed.")