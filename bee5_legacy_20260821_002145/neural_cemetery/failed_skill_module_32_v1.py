# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def extract_error_details(log_line: str) -> dict:
    """
    Parse a linker CFI error log line and return its components.

    Expected format (example):
        bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

    Returns a dictionary with keys:
        - file_path: str
        - line_number: int
        - check: str
        - condition: str
        - message: str (the trailing text after the condition, if any)

    If parsing fails, returns an empty dictionary.
    """
    import re

    pattern = (
        r"^(?P<file_path>[^:]+):"
        r"(?P<line_number>\d+):\s*"
        r"(?P<check>CHECK)\s*"
        r"'(?P<condition>[^']+)'"
        r"(?:\s*(?P<message>failed|error|warning).*)?$"
    )
    match = re.match(pattern, log_line.strip())
    if not match:
        return {}

    groups = match.groupdict()
    # Convert line_number to int
    groups["line_number"] = int(groups["line_number"])
    # Ensure optional message exists
    groups["message"] = groups.get("message") or ""
    return groups


if __name__ == "__main__":
    # Self‑test cases
    test_cases = [
        (
            "bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed",
            {
                "file_path": "bionic/linker/linker_cfi.cpp",
                "line_number": 158,
                "check": "CHECK",
                "condition": "p != MAP_FAILED",
                "message": "failed",
            },
        ),
        (
            "src/main.c:42: CHECK 'x > 0' error",
            {
                "file_path": "src/main.c",
                "line_number": 42,
                "check": "CHECK",
                "condition": "x > 0",
                "message": "error",
            },
        ),
        (
            "invalid line without proper format",
            {},
        ),
    ]

    for line, expected in test_cases:
        result = extract_error_details(line)
        if result != expected:
            raise AssertionError(f"Parsing failed for line: {line!r}\nExpected: {expected}\nGot: {result}")

    print("All tests passed.")