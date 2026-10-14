# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import re

def parse_size(size_str: str) -> int:
    """
    Parse a human‑readable size string and return the size in bytes.

    Supported units (case‑insensitive):
        B, KB, MB, GB, TB  (decimal, multiples of 1000)
        KiB, MiB, GiB, TiB (binary, multiples of 1024)

    The numeric part may be an integer or a decimal number.
    Whitespace around the string is ignored.

    Examples
    --------
    >>> parse_size("10B")
    10
    >>> parse_size("1KB")
    1000
    >>> parse_size("1KiB")
    1024
    >>> parse_size("2.5MB")
    2500000
    >>> parse_size("3.5MiB")
    3670016
    """
    if not isinstance(size_str, str):
        raise TypeError("size_str must be a string")

    s = size_str.strip()
    pattern = r'^([0-9]*\.?[0-9]+)\s*([KMGT]?i?B)$'
    match = re.fullmatch(pattern, s, re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid size format: '{size_str}'")

    number_str, unit = match.groups()
    number = float(number_str)

    unit = unit.upper()
    decimal_factors = {
        'B': 1,
        'KB': 1000,
        'MB': 1000 ** 2,
        'GB': 1000 ** 3,
        'TB': 1000 ** 4,
    }
    binary_factors = {
        'KIB': 1024,
        'MIB': 1024 ** 2,
        'GIB': 1024 ** 3,
        'TIB': 1024 ** 4,
    }

    if unit in decimal_factors:
        factor = decimal_factors[unit]
    elif unit in binary_factors:
        factor = binary_factors[unit]
    else:
        raise ValueError(f"Unsupported unit: '{unit}'")

    return int(number * factor)


if __name__ == "__main__":
    # Basic tests – will raise AssertionError on failure
    assert parse_size("10B") == 10
    assert parse_size("  1KB  ") == 1000
    assert parse_size("1KiB") == 1024
    assert parse_size("2.5MB") == 2500000
    assert parse_size("3.5MiB") == 3670016
    assert parse_size("5GB") == 5 * 1000 ** 3
    assert parse_size("5GiB") == 5 * 1024 ** 3
    assert parse_size("0.5TB") == int(0.5 * 1000 ** 4)
    assert parse_size("0.5TiB") == int(0.5 * 1024 ** 4)

    # Invalid inputs should raise ValueError
    for bad in ["", "abc", "10", "10XB", "10K", "10KBps"]:
        try:
            parse_size(bad)
            raise AssertionError(f"Expected ValueError for input: {bad}")
        except ValueError:
            pass

    # Non‑string input should raise TypeError
    try:
        parse_size(123)
        raise AssertionError("Expected TypeError for non‑string input")
    except TypeError:
        pass

    print("All tests passed.")