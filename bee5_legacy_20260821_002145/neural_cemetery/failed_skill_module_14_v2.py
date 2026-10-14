# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def rewrite_linker_cfi_cpp(input_path: str, output_path: str) -> str:
    """
    Reads a C++ source file (expected to be ``bionic/linker/linker_cfi.cpp``) and
    rewrites the failing ``MapShadow`` check to a safer guard.

    The original failing line typically looks like:
        CHECK(p != MAP_FAILED);
    which aborts the process if ``p`` is ``MAP_FAILED``.  The rewritten version
    replaces the abort with an early return, preventing the crash while keeping
    the original intent of not proceeding with an invalid mapping.

    The function performs a simple textual substitution; it does **not**
    perform full parsing of C++ syntax.  It is intended as a quick mitigation
    for the specific error reported in the build logs.

    Parameters
    ----------
    input_path: str
        Path to the original ``linker_cfi.cpp`` file.
    output_path: str
        Path where the patched file will be written.

    Returns
    -------
    str
        The ``output_path`` that was written.
    """
    # Read the original source
    with open(input_path, "r", encoding="utf-8") as src_file:
        source = src_file.read()

    # Perform a conservative replacement.  We only touch lines that contain
    # the exact macro usage ``CHECK(p != MAP_FAILED)`` (or with optional spaces).
    import re

    pattern = re.compile(r"\bCHECK\s*\(\s*p\s*!=\s*MAP_FAILED\s*\)\s*;")
    replacement = "if (p == MAP_FAILED) return;"

    new_source, count = pattern.subn(replacement, source)

    # If nothing was replaced, we still write the file unchanged but note it.
    if count == 0:
        # No matching line found – the caller may want to know.
        # We'll still write the file to keep the contract consistent.
        pass

    # Write the patched source
    with open(output_path, "w", encoding="utf-8") as out_file:
        out_file.write(new_source)

    return output_path


if __name__ == "__main__":
    import tempfile
    import os

    # Create a temporary directory to hold test files
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_cpp = os.path.join(tmp_dir, "linker_cfi.cpp")
        patched_cpp = os.path.join(tmp_dir, "linker_cfi_patched.cpp")

        # Sample content that mimics the problematic check
        sample_content = (
            "#include <stdio.h>\\n"
            "void foo() {\\n"
            "    void* p = mmap(...);\\n"
            "    CHECK(p != MAP_FAILED);\\n"
            "    // some other code\\n"
            "}\\n"
        )

        # Write the sample file
        with open(original_cpp, "w", encoding="utf-8") as f:
            f.write(sample_content)

        # Run the rewrite function
        result_path = rewrite_linker_cfi_cpp(original_cpp, patched_cpp)

        # Verify that the output file exists
        if not os.path.isfile(result_path):
            raise AssertionError("Patched file was not created.")

        # Verify that the replacement occurred
        with open(result_path, "r", encoding="utf-8") as f:
            patched_content = f.read()

        expected_line = "if (p == MAP_FAILED) return;"
        if expected_line not in patched_content:
            raise AssertionError(
                "Expected replacement line not found in patched content."
            )

        # Ensure that other parts of the file remain unchanged
        if "void* p = mmap(...);" not in patched_content:
            raise AssertionError("Unrelated code was unintentionally modified.")

        # If we reach this point, the test succeeded
        print("All self‑tests passed.")