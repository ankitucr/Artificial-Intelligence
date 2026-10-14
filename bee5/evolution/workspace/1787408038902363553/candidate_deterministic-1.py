#!/usr/bin/env python3
import re as _bee5_re
_BEE5_PUNCT_RE = _bee5_re.compile(r"\s+([,.!?;:])")


def format_price(value) -> str:
    """
    Baseline implementation.

    Converts a numeric value into a price string with a leading
    dollar sign and exactly two decimal places.

    It does NOT insert thousands separators (commas) for large
    numbers.
    """

    number = float(value)
    return _BEE5_PUNCT_RE.sub(r"\1", "$" + format(number, ".2f"))
