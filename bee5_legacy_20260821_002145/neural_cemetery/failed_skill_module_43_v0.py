# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def parse_iso8601_duration(duration: str) -> float:
    """
    Parse a subset of ISO 8601 duration strings and return the total duration in seconds.

    Supported format: P[n]Y[n]M[n]DT[n]H[n]M[n]S
    Only days, hours, minutes, and seconds are interpreted;
    years, months, and weeks are ignored (treated as zero) because their length is ambiguous.

    Example:
        "PT1H30M" -> 5400
        "P2DT3H4M5S" -> 183845

    Args:
        duration: ISO 8601 duration string.

    Returns:
        Total duration in seconds (float).

    Raises:
        ValueError: If the string is not a valid ISO 8601 duration.
    """
    import re

    if not isinstance(duration, str):
        raise TypeError("duration must be a string")

    pattern = re.compile(
        r'^P'                                   # starts with 'P'
        r'(?:(?P<years>\d+(\.\d+)?)Y)?'         # years (ignored)
        r'(?:(?P<months>\d+(\.\d+)?)M)?'        # months (ignored)
        r'(?:(?P<weeks>\d+(\.\d+)?)W)?'         # weeks (ignored)
        r'(?:(?P<days>\d+(\.\d+)?)D)?'          # days
        r'(?:T'                                 # time part begins with 'T'
        r'(?:(?P<hours>\d+(\.\d+)?)H)?'         # hours
        r'(?:(?P<minutes>\d+(\.\d+)?)M)?'       # minutes
        r'(?:(?P<seconds>\d+(\.\d+)?)S)?'       # seconds
        r')?$'
    )
    match = pattern.fullmatch(duration)
    if not match:
        raise ValueError(f"Invalid ISO 8601 duration: {duration}")

    total_seconds = 0.0
    parts = match.groupdict()

    # Days
    if parts.get('days'):
        total_seconds += float(parts['days']) * 86400
    # Hours
    if parts.get('hours'):
        total_seconds += float(parts['hours']) * 3600
    # Minutes
    if parts.get('minutes'):
        total_seconds += float(parts['minutes']) * 60
    # Seconds
    if parts.get('seconds'):
        total_seconds += float(parts['seconds'])

    return total_seconds


if __name__ == "__main__":
    # Simple self-test suite
    test_cases = {
        "PT0S": 0,
        "PT45S": 45,
        "PT1M": 60,
        "PT2M30S": 150,
        "PT1H": 3600,
        "PT1H30M": 5400,
        "P1D": 86400,
        "P2DT3H4M5S": 2 * 86400 + 3 * 3600 + 4 * 60 + 5,
        "P0DT0H0M0S": 0,
        "PT0.5S": 0.5,
        "P1DT0.5H": 86400 + 0.5 * 3600,
    }

    for iso_str, expected in test_cases.items():
        result = parse_iso8601_duration(iso_str)
        if abs(result - expected) > 1e-6:
            raise AssertionError(f"Failed for {iso_str}: expected {expected}, got {result}")

    # Test invalid inputs
    invalid_inputs = ["", "1H", "P-1D", "PT", "P", "P1Y2M3DT4H5M6S", "P1Y"]  # years/months ignored but format valid; last two are valid per regex (years/months ignored)
    for bad in invalid_inputs:
        try:
            parse_iso8601_duration(bad)
        except ValueError:
            continue
        else:
            raise AssertionError(f"Expected ValueError for invalid input '{bad}'")

    print("All tests passed.")