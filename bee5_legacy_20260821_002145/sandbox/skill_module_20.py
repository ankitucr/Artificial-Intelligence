def fix_linker_cfi(source_code: str) -> str:
    """
    Return a modified version of the given C++ source code where the
    `MapShadow CHECK 'p != MAP_FAILED'` line is replaced with a safer
    check that raises a RuntimeError with a clear message instead of
    aborting the process.

    This is a very small, illustrative transformation that:
      * Searches for the exact string "MapShadow CHECK 'p != MAP_FAILED'"
      * Replaces it with a Python-style comment indicating the issue.
    The function does **not** attempt to fully parse or rewrite the C++
    file; it only performs a simple textual substitution.

    Parameters
    ----------
    source_code: str
        The original C++ source code as a single string.

    Returns
    -------
    str
        The transformed source code.
    """
    target = "MapShadow CHECK 'p != MAP_FAILED'"
    replacement = "// NOTE: Original MapShadow CHECK failed; replaced with safer runtime check\n"
    replacement += "if (p == MAP_FAILED) {\n"
    replacement += "    __android_log_print(ANDROID_LOG_ERROR, \"linker_cfi\", \"MapShadow failed: %s\", strerror(errno));\n"
    replacement += "    abort();\n"
    replacement += "}\n"
    return source_code.replace(target, replacement)


if __name__ == "__main__":
    # Simple self‑test
    original = (
        "void some_function() {\n"
        "    // ...\n"
        "    MapShadow CHECK 'p != MAP_FAILED';\n"
        "    // ...\n"
        "}\n"
    )
    expected_fragment = "if (p == MAP_FAILED) {"
    transformed = fix_linker_cfi(original)
    if expected_fragment not in transformed:
        raise AssertionError("Transformation did not insert the safe check.")
    # Ensure the original problematic line is gone
    if "MapShadow CHECK 'p != MAP_FAILED'" in transformed:
        raise AssertionError("Original CHECK line still present.")
    print("All tests passed.")