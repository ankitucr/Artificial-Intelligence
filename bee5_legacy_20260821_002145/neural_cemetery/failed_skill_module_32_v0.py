# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def parse_duration(duration_str: str) -> int:
    """
    Convert a human‑readable duration string to a total number of seconds.

    Supported units (case‑insensitive):
        d – days
        h – hours
        m – minutes
        s – seconds

    Units may appear in any order, may be separated by whitespace, and may be
    concatenated without spaces (e.g., "2h30m").

    Examples
    --------
    >>> parse_duration("2h 30m")
    9000
    >>> parse_duration("1d2h3m4s")
    93784

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
        If the string contains an invalid format or unknown unit.
    """
    import re

    if not isinstance(duration_str, str):
        raise ValueError("duration_str must be a string")

    # Normalize: remove surrounding whitespace and make lower case
    cleaned = duration_str.strip().lower()
    if not cleaned:
        raise ValueError("Empty duration string")

    # Pattern matches sequences like "2h", "30m", etc.
    pattern = re.compile(r"(\d+\.?\d*)\s*([dhms])")
    matches = pattern.findall(cleaned)

    if not matches:
        raise ValueError(f"Invalid duration format: '{duration_str}'")

    total_seconds = 0
    unit_factors = {"d": 86400, "h": 3600, "m": 60, "s": 1}

    # To detect unsupported leftover characters, remove all matched parts
    # and ensure nothing non‑whitespace remains.
    consumed = "".join(f"{num}{unit}" for num, unit in matches)
    leftover = re.sub(pattern, "", cleaned).strip()
    if leftover:
        raise ValueError(f"Unrecognized part in duration string: '{leftover}'")

    for number_str, unit in matches:
        try:
            number = float(number_str)
        except ValueError as exc:
            raise ValueError(f"Invalid number '{number_str}'") from exc
        total_seconds += int(number * unit_factors[unit])

    return total_seconds


if __name__ == "__main__":
    # Basic correctness tests
    assert parse_duration("2h30m") == 9000
    assert parse_duration("  1d 2h 3m 4s  ") == 93784
    assert parse_duration("45s") == 45
    assert parse_duration("0d0h0m0s") == 0
    assert parse_duration("1.5h") == 5400  # 1.5 hours = 5400 seconds
    # Mixed order and spaces
    assert parse_duration("3m 1h") == 3780
    # Upper‑case support
    assert parse_duration("2H 5M") == 7500

    # Invalid inputs should raise ValueError
    for bad in ["", "   ", "abc", "10x", "5", "2h 30", "2h30x"]:
        try:
            parse_duration(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Expected ValueError for input: {bad}")

    print("All parse_duration tests passed.")