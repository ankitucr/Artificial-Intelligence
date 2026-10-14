# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def fix_linker_cfi(source_code: str) -> str:
    """
    Very small utility that attempts to "fix" a known issue in the Android bionic
    linker CFI source file. The original problem arises from a malformed CHECK
    macro invocation:

        CHECK 'p != MAP_FAILED'

    which should be a proper function‑style macro call:

        CHECK(p != MAP_FAILED)

    This function performs a simple textual replacement to correct the macro
    usage. It is deliberately lightweight and does not attempt to parse C++
    code; it only replaces the exact problematic pattern.

    Parameters
    ----------
    source_code: str
        The full text of the C++ source file to be fixed.

    Returns
    -------
    str
        The potentially corrected source code.
    """
    # The exact string we need to replace (including the space before the quote)
    problematic = "CHECK 'p != MAP_FAILED'"
    replacement = "CHECK(p != MAP_FAILED)"
    return source_code.replace(problematic, replacement)


if __name__ == "__main__":
    # Self‑test: ensure the replacement works as intended.
    original = (
        "#include <someheader.h>\\n"
        "void foo() {\\n"
        "    void *p = mmap(...);\\n"
        "    CHECK 'p != MAP_FAILED';\\n"
        "    // other code\\n"
        "}\\n"
    )
    expected = (
        "#include <someheader.h>\\n"
        "void foo() {\\n"
        "    void *p = mmap(...);\\n"
        "    CHECK(p != MAP_FAILED);\\n"
        "    // other code\\n"
        "}\\n"
    )
    result = fix_linker_cfi(original)
    if result != expected:
        raise AssertionError("fix_linker_cfi did not produce the expected output")
    # If we reach this point, the test passed.
    print("All tests passed.")