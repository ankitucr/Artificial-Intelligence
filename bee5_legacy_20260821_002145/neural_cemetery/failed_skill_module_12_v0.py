# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def extract_urls(text):
    """
    Extract all URLs from the given text string.

    Supports http, https, ftp schemes and also www-prefixed domains.
    Returns a list of URLs in the order they appear.
    """
    import re

    # Regex pattern to match URLs
    url_pattern = re.compile(
        r'(?i)\b('
        r'(?:https?://|ftp://)'                     # scheme
        r'(?:[\w\-]+\.)+[a-z]{2,}'                  # domain
        r'(?:[^\s\'"<>]*)'                          # optional path/query
        r'|'
        r'www\.(?:[\w\-]+\.)+[a-z]{2,}'             # www-prefixed domains
        r'(?:[^\s\'"<>]*)'                          # optional path/query
        r')'
    )
    return [match.group(0) for match in url_pattern.finditer(text)]


if __name__ == "__main__":
    # Test cases for extract_urls
    test_cases = [
        (
            "Visit our site at https://example.com for more info.",
            ["https://example.com"]
        ),
        (
            "Check http://sub.domain.org/path?query=1 and also www.test.co.uk/page.",
            ["http://sub.domain.org/path?query=1", "www.test.co.uk/page."]
        ),
        (
            "No URLs here!",
            []
        ),
        (
            "Mixed content: ftp://files.server.com/downloads/file.zip, and a plain text.",
            ["ftp://files.server.com/downloads/file.zip"]
        ),
        (
            "Multiple URLs: https://a.com https://b.org/path https://c.net?param=val",
            ["https://a.com", "https://b.org/path", "https://c.net?param=val"]
        ),
    ]

    for idx, (input_text, expected) in enumerate(test_cases, 1):
        result = extract_urls(input_text)
        # Strip trailing punctuation that may be attached to URLs in plain text
        result = [url.rstrip('.,;!') for url in result]
        expected = [url.rstrip('.,;!') for url in expected]
        if result != expected:
            raise AssertionError(f"Test case {idx} failed: expected {expected}, got {result}")

    print("All extract_urls tests passed.")