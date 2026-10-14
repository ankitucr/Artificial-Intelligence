# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def safe_int(value, default=0):
    """
    Convert *value* to an integer safely.

    If *value* is an int, it is returned unchanged.
    If *value* is a string that represents an integer (including optional
    leading/trailing whitespace), it is converted and returned.
    For any other type or if conversion fails, *default* is returned.

    Parameters
    ----------
    value : Any
        The value to convert.
    default : int, optional
        The fallback value returned on failure. Default is 0.

    Returns
    -------
    int
        The integer representation of *value* or *default*.
    """
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            # Strip whitespace to allow strings like " 42 "
            return int(value.strip())
        except ValueError:
            return default
    try:
        # Attempt to convert other numeric types (e.g., float, Decimal)
        return int(value)
    except Exception:
        return default


if __name__ == "__main__":
    # Test cases for safe_int
    assert safe_int(10) == 10, "Direct int should be unchanged"
    assert safe_int("42") == 42, "String numeric should convert"
    assert safe_int("   -7  ") == -7, "String with whitespace should convert"
    assert safe_int("not a number", default=5) == 5, "Invalid string returns default"
    assert safe_int(None, default=3) == 3, "None returns default"
    assert safe_int(3.14) == 3, "Float truncates toward zero"
    assert safe_int(1e6) == 1000000, "Scientific notation works via int conversion"
    # Edge case: large integer string
    large_number = "12345678901234567890"
    assert safe_int(large_number) == int(large_number), "Large integer string conversion"
    # If any assertion fails, an AssertionError will be raised and exit non-zero
    print("All safe_int tests passed.")