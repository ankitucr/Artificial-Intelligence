# Reviewer rejected: REJECTED: Test case uses ".join(_UNIT_MULTIPLIERS)" to serialize keys as comma-separated string, but unit determination could fail if some keys have spaces (e.g., if _UNIT_MULTIPLIERS contained both "KB" and "KB-legacy"). This existence check is insufficient but not a critical security violation per the original requirements. However, tuple keys requirement in rejection context conflicts with actual implementation's string keys, creating inconsistency.

"""Utility to parse human‑readable size strings into bytes and format bytes back to readable strings."""

import re
from typing import Tuple, Dict, Any

# Mapping of unit suffixes to their multiplier in bytes (binary units, base 1024)
_UNIT_MULTIPLIERS = {
    "B": 1,
    "KB": 1024,
    "MB": 1024 ** 2,
    "GB": 1024 ** 3,
    "TB": 1024 ** 4,
    "PB": 1024 ** 5,
    "EB": 1024 ** 6,
    "ZB": 1024 ** 7,
    "YB": 1024 ** 8,
}


def parse_size(size_str: str) -> int:
    """
    Convert a human‑readable size string (e.g. \"2.5 MB\", \"1024KB\") to an integer number of bytes.

    The function is case‑insensitive, allows an optional space between the number and the unit,
    and understands the units defined in ``_UNIT_MULTIPLIERS``. If the unit is omitted, bytes are assumed.
    """
    if not isinstance(size_str, str):
        raise TypeError("size_str must be a string")

    pattern = r"^\s*([0-9]*\.?[0-9]+)\s*([a-zA-Z]{0,2})\s*$"
    match = re.match(pattern, size_str)
    if not match:
        raise ValueError(f"Unable to parse size string: '{size_str}'")

    number_str, unit = match.groups()
    number = float(number_str)
    unit = (unit or "B").upper()

    if unit not in _UNIT_MULTIPLIERS:
        raise ValueError(f"Unsupported unit '{unit}'. Supported units: {', '.join(_UNIT_MULTIPLIERS)}")

    bytes_value = int(round(number * _UNIT_MULTIPLIERS[unit]))
    return bytes_value


def format_size(num_bytes: int, precision: int = 2) -> str:
    """
    Convert an integer number of bytes to a human‑readable string using the largest appropriate unit.

    ``precision`` controls the number of decimal places (default 2). Trailing zeros and an unnecessary
    decimal point are stripped for a cleaner output.
    """
    if not isinstance(num_bytes, int):
        raise TypeError("num_bytes must be an integer")
    if num_bytes < 0:
        raise ValueError("num_bytes must be non‑negative")

    if num_bytes == 0:
        return "0 B"

    # Find the largest unit where the value is >= 1
    for unit in reversed(list(_UNIT_MULTIPLIERS.keys())):
        multiplier = _UNIT_MULTIPLIERS[unit]
        if num_bytes >= multiplier:
            value = num_bytes / multiplier
            formatted = f"{value:.{precision}f} {unit}"
            # Strip unnecessary trailing zeros and possible trailing dot
            formatted = re.sub(r"\.?0+$", "", formatted)
            return formatted

    # Fallback (should never hit because 'B' is the smallest unit)
    return f"{num_bytes} B"


SAMPLE_ARGS = {"size_str": "2.5 MB"}


def run(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entry point for the skill.

    Expected keys in ``args``:
        - ``size_str``: a human‑readable size string to be parsed (optional).
        - ``bytes``: an integer number of bytes to be formatted (optional).

    The function returns a dictionary containing both representations:
        ``bytes`` – the parsed number of bytes (int).
        ``formatted`` – the size string formatted from the byte count (str).
    """
    # Determine the byte count
    if "size_str" in args and args["size_str"] is not None:
        bytes_val = parse_size(args["size_str"])
    elif "bytes" in args and args["bytes"] is not None:
        if not isinstance(args["bytes"], int):
            raise TypeError("bytes argument must be an integer")
        bytes_val = args["bytes"]
    else:
        raise ValueError("Either 'size_str' or 'bytes' must be provided in args.")

    # Produce the formatted string
    formatted_str = format_size(bytes_val)

    return {"bytes": bytes_val, "formatted": formatted_str}


if __name__ == "__main__":
    result = run(SAMPLE_ARGS)
    expected = {"bytes": 2621440, "formatted": "2.5 MB"}
    if result != expected:
        raise AssertionError(f"Test failed: got {result}, expected {expected}")
    print("All tests passed.")