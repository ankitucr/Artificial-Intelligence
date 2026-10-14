# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import os
import mmap
import tempfile

def safe_mmap(filepath: str, access: int = mmap.ACCESS_READ) -> mmap.mmap:
    """
    Memory‑map the given file safely.

    Parameters
    ----------
    filepath: str
        Path to the file to be memory‑mapped.
    access: int, optional
        mmap access flag (default ``mmap.ACCESS_READ``).

    Returns
    -------
    mmap.mmap
        A memory‑mapped object for the file.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    PermissionError
        If the file cannot be opened with the required permissions.
    OSError
        For any other OS‑level error (e.g., insufficient resources).
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    try:
        fd = os.open(filepath, os.O_RDONLY)
        try:
            size = os.path.getsize(filepath)
            if size == 0:
                # mmap cannot map empty files; return an empty bytes object instead.
                return mmap.mmap(-1, 0, access=access)
            return mmap.mmap(fd, length=0, access=access)
        finally:
            os.close(fd)
    except PermissionError:
        raise
    except OSError as exc:
        raise OSError(f"Failed to memory‑map {filepath!r}: {exc}") from exc

if __name__ == "__main__":
    # Self‑test: create a temporary file, write known content, mmap it and verify.
    test_content = b"Hello, safe mmap!\nSecond line."
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_name = tmp.name
        tmp.write(test_content)
        tmp.flush()

    try:
        mm = safe_mmap(tmp_name)
        try:
            # Verify length and content
            if len(mm) != len(test_content):
                raise AssertionError("Mapped length does not match original file size")
            if mm[:].tobytes() != test_content:
                raise AssertionError("Mapped content does not match original file content")
        finally:
            mm.close()
    finally:
        os.unlink(tmp_name)  # Clean up the temporary file

    # Test mapping an empty file (should not raise)
    with tempfile.NamedTemporaryFile(delete=False) as empty_tmp:
        empty_name = empty_tmp.name

    try:
        empty_mm = safe_mmap(empty_name)
        try:
            if len(empty_mm) != 0:
                raise AssertionError("Empty file mapping should have length 0")
        finally:
            empty_mm.close()
    finally:
        os.unlink(empty_name)

    # If we reach this point, all tests passed.
    print("All safe_mmap tests passed.")