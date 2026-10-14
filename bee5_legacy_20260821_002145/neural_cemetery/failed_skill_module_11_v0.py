# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import re
from typing import Tuple

def format_bytes(num_bytes: int, suffix: str = "B") -> str:
    """
    Convert a number of bytes into a human‑readable string using binary prefixes.
    Example: 1536 -> "1.50 KiB"
    """
    if num_bytes < 0:
        raise ValueError("num_bytes must be non‑negative")
    units = ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]
    i = 0
    value = float(num_bytes)
    while value >= 1024 and i < len(units) - 1:
        value /= 1024.0
        i += 1
    return f"{value:.2f} {units[i]}{suffix}" if i > 0 else f"{value:.0f} {suffix}"


def _parse_number_and_unit(s: str) -> Tuple[float, str]:
    """
    Helper to split a string like "2.5 MB" into (2.5, "MB").
    """
    s = s.strip()
    match = re.fullmatch(r"([0-9]*\.?[0-9]+)\s*([a-zA-Z]+)", s)
    if not match:
        raise ValueError(f"Invalid size string: {s!r}")
    number = float(match.group(1))
    unit = match.group(2).upper()
    return number, unit


def parse_size(size_str: str) -> int:
    """
    Parse a human‑readable size string into an integer number of bytes.
    Supports decimal (KB, MB, ...) and binary (KiB, MiB, ...) prefixes.
    Example: "1.5 KiB" -> 1536
    """
    number, unit = _parse_number_and_unit(size_str)

    # Define multipliers for both decimal (k, M, G...) and binary (Ki, Mi...)
    decimal_multipliers = {
        "B": 1,
        "KB": 10**3,
        "MB": 10**6,
        "GB": 10**9,
        "TB": 10**12,
        "PB": 10**15,
        "EB": 10**18,
    }
    binary_multipliers = {
        "B": 1,
        "KIB": 1024,
        "MIB": 1024**2,
        "GIB": 1024**3,
        "TIB": 1024**4,
        "PIB": 1024**5,
        "EIB": 1024**6,
    }

    # Normalize unit (allow optional trailing "B")
    if not unit.endswith("B"):
        unit += "B"

    if unit in binary_multipliers:
        multiplier = binary_multipliers[unit]
    elif unit in decimal_multipliers:
        multiplier = decimal_multipliers[unit]
    else:
        raise ValueError(f"Unrecognized unit: {unit!r}")

    bytes_val = number * multiplier
    return int(round(bytes_val))


if __name__ == "__main__":
    # Test format_bytes
    assert format_bytes(0) == "0 B"
    assert format_bytes(500) == "500 B"
    assert format_bytes(1023) == "1023 B"
    assert format_bytes(1024) == "1.00 KiB"
    assert format_bytes(1536) == "1.50 KiB"
    assert format_bytes(10 * 1024**2) == "10.00 MiB"

    # Test parse_size with binary prefixes
    assert parse_size("1 KiB") == 1024
    assert parse_size("1.5 KiB") == 1536
    assert parse_size("10 MiB") == 10 * 1024**2
    assert parse_size("0 B") == 0

    # Test parse_size with decimal prefixes
    assert parse_size("1 KB") == 1000
    assert parse_size("1.5 MB") == int(round(1.5 * 10**6))
    assert parse_size("2 GB") == 2 * 10**9

    # Mixed case and spaces
    assert parse_size("  2.5  mib  ") == int(round(2.5 * 1024**2))
    assert parse_size("3.2Gb") == int(round(3.2 * 10**9))

    # Round‑trip consistency for a range of values
    for bytes_val in [0, 1, 512, 1024, 1500, 2048, 5 * 1024**2, 123456789]:
        formatted = format_bytes(bytes_val)
        # Only test round‑trip for binary-prefixed strings (they contain KiB, MiB, …)
        if any(p in formatted for p in ["KiB", "MiB", "GiB", "TiB"]):
            parsed = parse_size(formatted)
            # Allow a difference of 1 byte due to rounding in the formatting step
            assert abs(parsed - bytes_val) <= 1, f"Round‑trip failed for {bytes_val}"
    print("All tests passed.")