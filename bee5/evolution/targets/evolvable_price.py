#!/usr/bin/env python3

def format_price(value) -> str:
    """
    Baseline implementation.

    Converts a numeric value into a price string with a leading
    dollar sign and exactly two decimal places.

    It does NOT insert thousands separators (commas) for large
    numbers.
    """

    number = float(value)
    return "$" + format(number, ".2f")
