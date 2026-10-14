import re
from typing import Dict, Optional


def parse_linker_cfi_error(error: str) -> Optional[Dict[str, str]]:
    """
    Parse a bionic linker CFI (Control Flow Integrity) error message.

    Expected format (example):
        bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

    Returns a dictionary with the following keys if parsing succeeds:
        - file: the source file path
        - line: the line number as a string
        - check: the condition inside the CHECK macro
        - message: the remainder of the message after "failed"

    If the string does not match the expected pattern, returns None.
    """
    pattern = re.compile(
        r"""^\s*
        (?P<file>[^:\s]+)          # file path (no colon)
        :(?P<line>\d+):\s*         # line number
        (?P<check_name>\w+)\s+     # macro name, e.g., CHECK
        (?P<condition>'.+?')\s+   # condition in single quotes
        failed\s*
        (?P<msg>.*)                # optional trailing message
        $""",
        re.VERBOSE,
    )
    match = pattern.match(error)
    if not match:
        return None

    return {
        "file": match.group("file"),
        "line": match.group("line"),
        "check": match.group("condition").strip("'"),
        "message": match.group("msg").strip(),
    }


def suggest_cfi_fix(parsed: Dict[str, str]) -> str:
    """
    Given a parsed CFI error dictionary, return a short suggestion string.

    The suggestion is heuristic and focuses on the most common cause:
    a failed MAP_SHADOW CHECK indicates that a memory mapping operation returned MAP_FAILED.
    """
    check = parsed.get("check", "")
    if "p != MAP_FAILED" in check:
        return (
            f"The check '{check}' failed at {parsed['file']}:{parsed['line']}. "
            "This usually means a memory mapping (mmap) call returned MAP_FAILED. "
            "Ensure that the target address range is valid, the file descriptor is correct, "
            "and that the process has sufficient permissions/resources."
        )
    return (
        f"The check '{check}' failed at {parsed['file']}:{parsed['line']}. "
        "Review the condition and surrounding code for potential issues."
    )


if __name__ == "__main__":
    # Self‑test cases
    test_cases = [
        (
            "bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed",
            {
                "file": "bionic/linker/linker_cfi.cpp",
                "line": "158",
                "check": "p != MAP_FAILED",
                "message": "",
            },
            "The check 'p != MAP_FAILED' failed at bionic/linker/linker_cfi.cpp:158. This usually means a memory mapping (mmap) call returned MAP_FAILED. Ensure that the target address range is valid, the file descriptor is correct, and that the process has sufficient permissions/resources.",
        ),
        (
            "src/module.c:42: SomeMacro CHECK 'x > 0' failed extra info here",
            {
                "file": "src/module.c",
                "line": "42",
                "check": "x > 0",
                "message": "extra info here",
            },
            "The check 'x > 0' failed at src/module.c:42. Review the condition and surrounding code for potential issues.",
        ),
        ("invalid format string", None, None),
    ]

    for idx, (inp, expected_parsed, expected_suggestion) in enumerate(test_cases, 1):
        result = parse_linker_cfi_error(inp)
        if expected_parsed is None:
            if result is not None:
                raise AssertionError(f"Test {idx}: Expected None parsing, got {result}")
            continue
        if result != expected_parsed:
            raise AssertionError(f"Test {idx}: Parsing mismatch.\nGot: {result}\nExpected: {expected_parsed}")

        suggestion = suggest_cfi_fix(result)
        if suggestion != expected_suggestion:
            raise AssertionError(f"Test {idx}: Suggestion mismatch.\nGot: {suggestion}\nExpected: {expected_suggestion}")

    print("All tests passed.")