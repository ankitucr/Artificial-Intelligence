# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def fix_mapshadow_check(source: str) -> str:
    """
    Replace occurrences of the Bionic MAP_SHADOW CHECK macro with a more
    robust runtime check.

    The original pattern looks like:
        MapShadow CHECK 'p != MAP_FAILED' failed

    This function replaces it with a C++ idiom that checks the pointer and
    aborts with a descriptive error message if the mapping failed.

    Parameters
    ----------
    source: str
        The original C++ source code.

    Returns
    -------
    str
        The transformed source code.
    """
    import re

    # Pattern to match the specific CHECK macro usage. It may appear in a
    # comment or as part of a macro expansion. We look for the literal text
    # "CHECK 'p != MAP_FAILED'" possibly surrounded by whitespace.
    pattern = re.compile(
        r"""(?P<indent>\s*)          # capture leading indentation
            (?:#\s*)?                # optional preprocessor comment marker
            CHECK\s*'p\s*!=\s*MAP_FAILED'  # the macro text
        """,
        re.VERBOSE,
    )

    def replacer(match):
        indent = match.group("indent") or ""
        replacement = (
            f"{indent}if (p == MAP_FAILED) {{\n"
            f"{indent}    perror(\"mmap\");\n"
            f"{indent}    abort();\n"
            f"{indent}}}"
        )
        return replacement

    # Apply replacement globally
    transformed = pattern.sub(replacer, source)

    # Additionally, handle the specific error message that might appear in a
    # comment like "MapShadow CHECK 'p != MAP_FAILED' failed". Replace the
    # entire comment with the same robust check.
    comment_pattern = re.compile(
        r"""(?P<indent>\s*)                # leading indentation
            //\s*MapShadow\s+CHECK\s+'p\s*!=\s*MAP_FAILED'\s+failed
        """,
        re.VERBOSE,
    )

    def comment_replacer(match):
        indent = match.group("indent") or ""
        return (
            f"{indent}if (p == MAP_FAILED) {{\n"
            f"{indent}    perror(\"mmap\");\n"
            f"{indent}    abort();\n"
            f"{indent}}}"
        )

    transformed = comment_pattern.sub(comment_replacer, transformed)

    return transformed


if __name__ == "__main__":
    # Simple self‑test
    original = (
        "    // MapShadow CHECK 'p != MAP_FAILED' failed\\n"
        "    // Some other comment\\n"
        "    CHECK 'p != MAP_FAILED'\\n"
        "    int x = 42;\\n"
    )
    expected = (
        "    if (p == MAP_FAILED) {\\n"
        "        perror(\"mmap\");\\n"
        "        abort();\\n"
        "    }\\n"
        "    // Some other comment\\n"
        "    if (p == MAP_FAILED) {\\n"
        "        perror(\"mmap\");\\n"
        "        abort();\\n"
        "    }\\n"
        "    int x = 42;\\n"
    )
    result = fix_mapshadow_check(original)
    if result != expected:
        raise AssertionError(
            f"Transformation failed.\\nExpected:\\n{expected}\\nGot:\\n{result}"
        )
    print("All tests passed.")