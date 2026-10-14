# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def slugify(text: str, separator: str = '-') -> str:
    """
    Convert a string to a URL-friendly slug.

    Steps:
    1. Normalize to lowercase.
    2. Replace any character that is not alphanumeric with the separator.
    3. Collapse multiple consecutive separators into one.
    4. Strip leading and trailing separators.

    Parameters
    ----------
    text : str
        The input string to slugify.
    separator : str, optional
        The separator to use for non‑alphanumeric characters, by default '-'.

    Returns
    -------
    str
        The slugified version of the input string.
    """
    import unicodedata
    import re

    # Normalize Unicode characters to their closest ASCII representation
    normalized = unicodedata.normalize('NFKD', text)
    ascii_bytes = normalized.encode('ascii', 'ignore')
    ascii_str = ascii_bytes.decode('ascii')

    # Lowercase
    lowercased = ascii_str.lower()

    # Replace non-alphanumeric characters with separator
    replaced = re.sub(r'[^a-z0-9]+', separator, lowercased)

    # Collapse multiple separators
    collapsed = re.sub(rf'{re.escape(separator)}{{2,}}', separator, replaced)

    # Strip leading/trailing separators
    slug = collapsed.strip(separator)

    return slug


if __name__ == "__main__":
    # Basic cases
    assert slugify("Hello World!") == "hello-world"
    assert slugify("Python's   __init__ method") == "python-s-init-method"
    assert slugify("  Leading and trailing  ") == "leading-and-trailing"
    assert slugify("Multiple---dashes") == "multiple-dashes"
    assert slugify("Café Münchner Kindl") == "cafe-munchner-kindl"
    # Custom separator
    assert slugify("Hello World!", separator="_") == "hello_world"
    # Edge cases
    assert slugify("") == ""
    assert slugify("---") == ""
    # Unicode edge case
    assert slugify("Δelta Σigma") == "elta-mma"

    # If any assertion fails, the script will exit with a non-zero status.
    print("All slugify tests passed.")