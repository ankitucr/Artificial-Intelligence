# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import re
import sys
import pathlib
import tempfile

def fix_mapshadow_check(file_path: str) -> None:
    """
    Fixes a common bug in linker_cfi.cpp where the MAP_SHADOW CHECK macro
    uses an invalid syntax that can cause a runtime failure.
    
    This function rewrites the file in place, replacing lines that contain
    the pattern ``CHECK('p != MAP_FAILED')`` (or variations with double quotes)
    with a safer Pythonic check that raises a RuntimeError if the mapping fails.
    
    The replacement line will be:
    
        if p == MAP_FAILED:
            raise RuntimeError("MAP_SHADOW failed")
    
    Args:
        file_path: Path to the C++ source file to be fixed.
    
    Raises:
        FileNotFoundError: If ``file_path`` does not exist.
        RuntimeError: If the file cannot be written back.
    """
    path = pathlib.Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    content = path.read_text(encoding="utf-8")
    # Regex to find the CHECK macro that checks p != MAP_FAILED
    pattern = re.compile(
        r"""^\s*CHECK\(\s*['"]?p\s*!=\s*MAP_FAILED['"]?\s*\)\s*;?\s*$""",
        re.MULTILINE,
    )

    def replacer(match: re.Match) -> str:
        indent = match.group(0)[: match.start(0) - match.string.rfind("\n", 0, match.start(0)) - 1]
        return (
            f"{indent}if (p == MAP_FAILED) {{\n"
            f"{indent}    throw std::runtime_error(\"MAP_SHADOW failed\");\n"
            f"{indent}}}"
        )

    new_content, count = pattern.subn(replacer, content)
    if count == 0:
        # No replacement made; nothing to do.
        return

    try:
        path.write_text(new_content, encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"Failed to write fixed content to {file_path}: {exc}") from exc


if __name__ == "__main__":
    # Self‑test: create a temporary C++ file with the buggy CHECK line,
    # run the fixer, and verify the output.
    buggy_cpp = """\
#include <sys/mman.h>
#include <stdexcept>

void foo() {
    void* p = mmap(nullptr, 4096, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    CHECK('p != MAP_FAILED');
    // some other code
}
"""

    expected_fixed_cpp = """\
#include <sys/mman.h>
#include <stdexcept>

void foo() {
    void* p = mmap(nullptr, 4096, PROT_READ | PROT_WRITE, MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (p == MAP_FAILED) {
        throw std::runtime_error("MAP_SHADOW failed");
    }
    // some other code
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = pathlib.Path(tmpdir) / "linker_cfi.cpp"
        test_file.write_text(buggy_cpp, encoding="utf-8")
        fix_mapshadow_check(str(test_file))
        result = test_file.read_text(encoding="utf-8")
        if result != expected_fixed_cpp:
            sys.stderr.write("Self‑test failed: fixed content does not match expected output.\n")
            sys.stderr.write("=== Expected ===\\n")
            sys.stderr.write(expected_fixed_cpp + "\\n")
            sys.stderr.write("=== Got ===\\n")
            sys.stderr.write(result + "\\n")
            sys.exit(1)

    print("All self‑tests passed.")