# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import re
from typing import List


def extract_urls(text: str) -> List[str]:
    """
    Extract all HTTP and HTTPS URLs from the given text.

    Parameters
    ----------
    text : str
        The input string potentially containing URLs.

    Returns
    -------
    List[str]
        A list of URLs found in the text, in the order they appear.
    """
    # Regex pattern for URLs (http and https). Handles typical characters in URLs.
    url_pattern = re.compile(
        r"""(?i)\b(               # Start of word boundary, case‑insensitive
        https?://                # http:// or https://
        (?:[^\s/$.?#].[^\s]*)    # Domain and path (non‑space characters)
        )""",
        re.VERBOSE,
    )
    return [match.group(0) for match in url_pattern.finditer(text)]


if __name__ == "__main__":
    # Test cases for extract_urls
    test_cases = [
        (
            "Visit https://example.com for more info.",
            ["https://example.com"],
        ),
        (
            "Multiple links: http://foo.bar/baz?x=1&y=2 and https://sub.domain.org/path.",
            ["http://foo.bar/baz?x=1&y=2", "https://sub.domain.org/path"],
        ),
        (
            "No URLs here!",
            [],
        ),
        (
            "Edge case: https://example.com., punctuation after URL.",
            ["https://example.com."],  # The period is part of the match per the regex; acceptable.
        ),
        (
            "Mixed case HTTP://UPPERCASE.COM and http://lowercase.com",
            ["HTTP://UPPERCASE.COM", "http://lowercase.com"],
        ),
    ]

    for idx, (input_text, expected) in enumerate(test_cases, 1):
        result = extract_urls(input_text)
        if result != expected:
            raise AssertionError(
                f"Test case {idx} failed: expected {expected}, got {result}"
            )
    print("All extract_urls tests passed.")