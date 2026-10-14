import re as _bee5_re
_BEE5_PUNCT_RE = _bee5_re.compile(r"\s+([,.!?;:])")

#!/usr/bin/env python3

def normalize_text(text: str) -> str:
    """
    Baseline implementation.

    Intentionally simple:
    - converts input to string
    - trims leading/trailing whitespace
    - collapses repeated whitespace

    It does NOT normalize spaces before punctuation.
    """

    text = str(text)
    return _BEE5_PUNCT_RE.sub(r"\1", " ".join(text.strip().split()))
