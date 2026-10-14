# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import re
import sys
from typing import List, Tuple


def find_mapshadow_failure(log: str) -> List[Tuple[int, str]]:
    """
    Scan a build log and return a list of occurrences where the MapShadow
    CHECK 'p != MAP_FAILED' failed.

    Each entry in the returned list is a tuple (line_number, line_text) where
    ``line_number`` is 1‑based.

    Parameters
    ----------
    log: str
        The complete log as a single string.

    Returns
    -------
    List[Tuple[int, str]]
        A list of matching lines with their line numbers. The list is empty if
        no matches are found.
    """
    pattern = re.compile(r"MapShadow\s+CHECK\s+'p\s*!=\s*MAP_FAILED'\s+failed", re.IGNORECASE)
    matches: List[Tuple[int, str]] = []
    for i, line in enumerate(log.splitlines(), start=1):
        if pattern.search(line):
            matches.append((i, line.rstrip()))
    return matches


def extract_failure_context(log: str, line_no: int, context: int = 2) -> List[str]:
    """
    Return a snippet of the log surrounding a failure line.

    Parameters
    ----------
    log: str
        The full log.
    line_no: int
        1‑based line number of the failure.
    context: int
        Number of lines before and after the failure line to include.

    Returns
    -------
    List[str]
        The extracted lines, each ending with a newline.
    """
    lines = log.splitlines(keepends=True)
    start = max(line_no - context - 1, 0)
    end = min(line_no + context, len(lines))
    return lines[start:end]


def summarize_failures(log: str) -> str:
    """
    Produce a human‑readable summary of all MapShadow failures in the log.

    Parameters
    ----------
    log: str
        The full build log.

    Returns
    -------
    str
        A multi‑line string summarising each failure with surrounding context.
    """
    failures = find_mapshadow_failure(log)
    if not failures:
        return "No MapShadow CHECK failures found."

    summary_parts = []
    for line_no, line_text in failures:
        context_lines = extract_failure_context(log, line_no)
        summary_parts.append(
            f"Failure at line {line_no}:\n"
            + "".join(context_lines)
        )
    return "\n".join(summary_parts)


if __name__ == "__main__":
    # Self‑test
    sample_log = """\
[100%] Linking CXX executable myapp
bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed
    at com.example.MyClass.method(MyClass.java:42)
bionic/linker/linker_cfi.cpp:200: Some other message
bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed
"""
    # Expected two failures at lines 2 and 5
    failures = find_mapshadow_failure(sample_log)
    if len(failures) != 2:
        raise AssertionError(f"Expected 2 failures, found {len(failures)}")
    if failures[0][0] != 2 or failures[1][0] != 5:
        raise AssertionError(f"Incorrect line numbers: {failures}")

    summary = summarize_failures(sample_log)
    if "Failure at line 2" not in summary or "Failure at line 5" not in summary:
        raise AssertionError("Summary does not contain expected failure entries")

    # Print summary for manual inspection (not required for the test)
    sys.stdout.write(summary)