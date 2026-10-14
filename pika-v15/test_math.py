def divide_numbers(a, b):
    """
    Divide a by b, handling division by zero gracefully.

    Parameters
    ----------
    a : numeric
        Numerator.
    b : numeric
        Denominator.

    Returns
    -------
    float
        The result of a / b if b is not zero.
    None
        If b is zero, indicating an undefined result.
    """
    if b == 0:
        # Avoid ZeroDivisionError; you could also raise an exception instead.
        return None
    return a / b

# Function ko deliberately crash karwayenge
divide_numbers(10, 0)
