# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def extract_urls(text):
    """
    Extract all HTTP/HTTPS URLs from the given text.

    Parameters
    ----------
    text : str
        Input string possibly containing URLs.

    Returns
    -------
    list of str
        List of URLs found in the text, in the order they appear.
    """
    import re

    # Regex pattern:
    # - starts with http or https
    # - ://
    # - then any characters that are not whitespace or punctuation that typically ends a URL
    #   We'll be permissive and stop at whitespace.
    pattern = re.compile(r'https?://[^\s]+')
    matches = pattern.findall(text)

    # Strip trailing punctuation that is unlikely part of the URL
    cleaned = []
    for url in matches:
        # Common trailing characters that may follow a URL in prose
        while url and url[-1] in '.,;:!?)]}\'"':
            url = url[:-1]
        cleaned.append(url)
    return cleaned


if __name__ == "__main__":
    # Basic sanity tests
    test_cases = [
        ("Visit https://example.com for more info.", ["https://example.com"]),
        ("Multiple URLs: http://a.com, https://b.org/path?x=1.", ["http://a.com", "https://b.org/path?x=1"]),
        ("No URL here!", []),
        ("Edge case: https://example.com.", ["https://example.com"]),
        ("Mixed punctuation https://example.com/page), and more.", ["https://example.com/page"]),
    ]

    for idx, (input_text, expected) in enumerate(test_cases, 1):
        result = extract_urls(input_text)
        if result != expected:
            raise AssertionError(f"Test case {idx} failed: expected {expected}, got {result}")

    # Large random test
    large_text = " ".join([
        "Check", "out", "https://site1.com.", "Also", "see", "http://site2.org/path,", 
        "and", "don't", "forget", "https://sub.domain.co.uk/page?query=val."
    ])
    expected_large = [
        "https://site1.com",
        "http://site2.org/path",
        "https://sub.domain.co.uk/page?query=val"
    ]
    if extract_urls(large_text) != expected_large:
        raise AssertionError("Large text test failed")

    print("All tests passed.")