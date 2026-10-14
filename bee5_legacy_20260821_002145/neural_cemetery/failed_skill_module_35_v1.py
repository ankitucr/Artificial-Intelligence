# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import re
import sys
from pathlib import Path

def fix_linker_cfi(file_path: str) -> None:
    """
    Fixes the MapShadow CHECK failure in bionic/linker/linker_cfi.cpp by replacing
    the macro-based CHECK with an explicit runtime check that aborts if the mapping
    fails. This avoids the use of the CHECK macro which may abort before proper
    cleanup and can be problematic in some build configurations.

    The function:
    - Reads the file.
    - Replaces occurrences of ``CHECK(p != MAP_FAILED)`` (or variants with
      whitespace) with an explicit ``if (p == MAP_FAILED) abort();`` statement.
    - Writes the modified content back to the same file.

    Parameters
    ----------
    file_path: str
        Path to the ``linker_cfi.cpp`` source file.

    Raises
    ------
    FileNotFoundError
        If the provided path does not exist.
    RuntimeError
        If the file does not contain any CHECK that matches the pattern, indicating
        that the expected code may have changed.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = path.read_text(encoding="utf-8")

    # Pattern matches CHECK ( optional whitespace ) ( p != MAP_FAILED )
    pattern = re.compile(r'\bCHECK\s*\(\s*p\s*!=\s*MAP_FAILED\s*\)', re.MULTILINE)
    if not pattern.search(content):
        raise RuntimeError("No matching CHECK(p != MAP_FAILED) found in the file.")

    replacement = "if (p == MAP_FAILED) abort();"
    new_content = pattern.sub(replacement, content)

    # Preserve original line endings
    line_ending = "\n"
    if "\r\n" in content:
        line_ending = "\r\n"
    new_content = new_content.replace("\n", line_ending)

    path.write_text(new_content, encoding="utf-8")


if __name__ == "__main__":
    # Self‑test: create a temporary source file, run the fixer, and verify the change.
    import tempfile

    original_cpp = """\
#include <unistd.h>
#include <sys/mman.h>

void foo() {
    void* p = mmap(nullptr, 4096, PROT_READ, MAP_PRIVATE, -1, 0);
    CHECK(p != MAP_FAILED);
    // Some other code
}
"""

    expected_cpp = """\
#include <unistd.h>
#include <sys/mman.h>

void foo() {
    void* p = mmap(nullptr, 4096, PROT_READ, MAP_PRIVATE, -1, 0);
    if (p == MAP_FAILED) abort();
    // Some other code
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "linker_cfi.cpp"
        test_file.write_text(original_cpp, encoding="utf-8")

        try:
            fix_linker_cfi(str(test_file))
        except Exception as e:
            sys.exit(f"Fixer raised an unexpected exception: {e}")

        result = test_file.read_text(encoding="utf-8")
        if result != expected_cpp:
            sys.exit("Self‑test failed: output does not match expected transformation.")
    # If we reach here, all tests passed.
    print("All tests passed.")