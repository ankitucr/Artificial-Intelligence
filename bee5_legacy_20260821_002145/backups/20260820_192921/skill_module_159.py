def modular_pow(base: int, exponent: int, modulus: int) -> int:
    """Return (base ** exponent) % modulus using binary exponentiation.

    Args:
        base: The base integer (can be negative).
        exponent: Non‑negative exponent.
        modulus: Positive modulus.
    Returns:
        The modular exponentiation result.
    """
    if modulus <= 0:
        raise ValueError("modulus must be a positive integer")
    if exponent < 0:
        raise ValueError("exponent must be non‑negative")
    result = 1 % modulus
    base = base % modulus
    while exponent:
        if exponent & 1:
            result = (result * base) % modulus
        exponent >>= 1
        base = (base * base) % modulus
    return result