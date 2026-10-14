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
    return " ".join(text.strip().split())
