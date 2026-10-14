# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def parse_cfi_error(log_line: str) -> dict:
    """
    Parse a CFI (Control Flow Integrity) error log line.

    Expected format:
        <path>:<line_number>: <message>

    Returns a dictionary with keys:
        - file: the file path as a string
        - line: the line number as an int
        - message: the error message as a string

    If the line cannot be parsed, returns an empty dictionary.
    """
    import re

    pattern = r"^(?P<file>.+?):(?P<line>\d+):\s*(?P<message>.+)$"
    match = re.match(pattern, log_line.strip())
    if not match:
        return {}

    return {
        "file": match.group("file"),
        "line": int(match.group("line")),
        "message": match.group("message"),
    }


def format_cfi_error(parsed: dict) -> str:
    """
    Reconstruct a CFI error log line from a parsed dictionary.

    The dictionary should contain 'file', 'line', and 'message' keys.
    Missing keys raise a ValueError.
    """
    required_keys = {"file", "line", "message"}
    if not required_keys.issubset(parsed):
        raise ValueError(f"Parsed dict missing required keys: {required_keys - set(parsed)}")
    return f"{parsed['file']}:{parsed['line']}: {parsed['message']}"


if __name__ == "__main__":
    # Test cases
    test_line = "bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed"
    expected = {
        "file": "bionic/linker/linker_cfi.cpp",
        "line": 158,
        "message": "MapShadow CHECK 'p != MAP_FAILED' failed",
    }

    result = parse_cfi_error(test_line)
    if result != expected:
        raise AssertionError(f"parse_cfi_error failed: got {result}, expected {expected}")

    reconstructed = format_cfi_error(result)
    if reconstructed != test_line:
        raise AssertionError(f"format_cfi_error failed: got '{reconstructed}', expected '{test_line}'")

    # Additional edge case: malformed line should return empty dict
    malformed = "this is not a valid log line"
    if parse_cfi_error(malformed) != {}:
        raise AssertionError("parse_cfi_error should return empty dict for malformed input")

    print("All tests passed.")