# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import re
import sys
import pathlib
import tempfile
import textwrap

def fix_linker_cfi_cpp(source_path: pathlib.Path) -> None:
    """
    Read a C++ source file (expected to be linker_cfi.cpp) and replace
    unsafe ``CHECK('p != MAP_FAILED')`` statements with a more robust
    runtime check that prints the errno and aborts with a clear message.

    The transformation is idempotent – running it multiple times will not
    duplicate the guard.

    Parameters
    ----------
    source_path: pathlib.Path
        Path to the ``linker_cfi.cpp`` file to be fixed.
    """
    if not source_path.is_file():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    text = source_path.read_text(encoding="utf-8")

    # Pattern to match the original CHECK macro usage.
    # Example:  CHECK(p != MAP_FAILED);
    check_pattern = re.compile(
        r"""(?P<indent>\s*)          # leading whitespace
            CHECK\s*\(\s*           # CHECK(
            (?P<expr>[^)]+)          # expression inside
            \s*\)\s*;               # );
        """,
        re.VERBOSE,
    )

    def replacement(match: re.Match) -> str:
        indent = match.group("indent")
        expr = match.group("expr").strip()
        # Only transform checks that compare a variable to MAP_FAILED.
        if not re.search(r"\bMAP_FAILED\b", expr):
            return match.group(0)  # leave unchanged

        # Extract the variable name on the left side of the comparison.
        var_match = re.match(r"(?P<var>\w+)\s*!=\s*MAP_FAILED", expr)
        if not var_match:
            var_match = re.match(r"MAP_FAILED\s*!=\s*(?P<var>\w+)", expr)
        if not var_match:
            return match.group(0)  # unexpected format; skip

        var_name = var_match.group("var")

        # Build a safe guard that prints strerror(errno) before aborting.
        guard = textwrap.dedent(f\"\"\"\
            {indent}if ({var_name} == MAP_FAILED) {{
            {indent}    int saved_errno = errno;
            {indent}    __android_log_print(ANDROID_LOG_FATAL, "linker_cfi", "mmap failed: %s", strerror(saved_errno));
            {indent}    abort();
            {indent}}}
            \"\"\")
        return guard

    new_text = check_pattern.sub(replacement, text)

    # Write back only if changes occurred.
    if new_text != text:
        source_path.write_text(new_text, encoding="utf-8")

def _run_self_test() -> None:
    """
    Self‑test for ``fix_linker_cfi_cpp``.

    1. Creates a temporary ``linker_cfi.cpp`` containing a typical CHECK line.
    2. Runs the fixer.
    3. Verifies that the CHECK line has been replaced by the robust guard.
    4. Ensures that running the fixer again is idempotent.
    """
    original_cpp = textwrap.dedent(\"\"\"\
        #include <sys/mman.h>
        #include <errno.h>
        #include <android/log.h>

        void foo() {
            void* p = mmap(nullptr, 4096, PROT_READ, MAP_PRIVATE, -1, 0);
            CHECK(p != MAP_FAILED);
        }
        \"\"\")

    expected_cpp = textwrap.dedent(\"\"\"\
        #include <sys/mman.h>
        #include <errno.h>
        #include <android/log.h>

        void foo() {
            void* p = mmap(nullptr, 4096, PROT_READ, MAP_PRIVATE, -1, 0);
            if (p == MAP_FAILED) {
                int saved_errno = errno;
                __android_log_print(ANDROID_LOG_FATAL, "linker_cfi", "mmap failed: %s", strerror(saved_errno));
                abort();
            }
        }
        \"\"\")

    with tempfile.TemporaryDirectory() as tmpdir:
        cpp_path = pathlib.Path(tmpdir) / "linker_cfi.cpp"
        cpp_path.write_text(original_cpp, encoding="utf-8")

        # First run – should transform the file.
        fix_linker_cfi_cpp(cpp_path)
        after_first = cpp_path.read_text(encoding="utf-8")
        if after_first != expected_cpp:
            raise AssertionError("First transformation did not produce expected output.")

        # Second run – should be idempotent (no further changes).
        fix_linker_cfi_cpp(cpp_path)
        after_second = cpp_path.read_text(encoding="utf-8")
        if after_second != expected_cpp:
            raise AssertionError("Second transformation altered the file unexpectedly.")

if __name__ == "__main__":
    _run_self_test()
    print("All self‑tests passed.")