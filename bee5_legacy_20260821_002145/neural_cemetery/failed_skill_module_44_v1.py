# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def parse_error_line(line: str) -> dict:
    """
    Parse a typical C++/C error log line of the form:
        path/to/file.cpp:123: error message

    Returns a dictionary with keys:
        - file: the file path as a string
        - line: the line number as an int (or None if not present)
        - message: the remaining error message as a string (may be empty)

    The function is tolerant of extra colons in the message part.
    """
    if not isinstance(line, str):
        raise TypeError("line must be a string")
    # Split only on the first two colons to separate file and line number
    parts = line.split(":", 2)
    if len(parts) < 2:
        # Not enough parts; treat the whole line as message with unknown file/line
        return {"file": None, "line": None, "message": line.strip()}
    file_part = parts[0].strip()
    line_part = parts[1].strip()
    message_part = parts[2].strip() if len(parts) == 3 else ""
    # Try converting line number to int
    try:
        line_num = int(line_part)
    except ValueError:
        # If conversion fails, treat it as part of the message
        line_num = None
        message_part = f"{line_part}: {message_part}".strip()
    return {"file": file_part or None, "line": line_num, "message": message_part}


if __name__ == "__main__":
    # Test cases
    tests = [
        (
            "bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed",
            {"file": "bionic/linker/linker_cfi.cpp", "line": 158,
             "message": "MapShadow CHECK 'p != MAP_FAILED' failed"}
        ),
        (
            "/path/to/source.c:42: warning: variable 'x' is unused",
            {"file": "/path/to/source.c", "line": 42,
             "message": "warning: variable 'x' is unused"}
        ),
        (
            "no_colon_here",
            {"file": None, "line": None, "message": "no_colon_here"}
        ),
        (
            "justfile.cpp:NotANumber: Something went wrong",
            {"file": "justfile.cpp", "line": None,
             "message": "NotANumber: Something went wrong"}
        ),
        (
            "module.cpp:100:",
            {"file": "module.cpp", "line": 100, "message": ""}
        ),
    ]

    for idx, (inp, expected) in enumerate(tests, 1):
        result = parse_error_line(inp)
        if result != expected:
            raise AssertionError(f"Test {idx} failed: expected {expected}, got {result}")
    print("All tests passed.")