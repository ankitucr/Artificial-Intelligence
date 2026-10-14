import mmap
import os
import sys
from typing import Optional


def map_file_readonly(file_path: str) -> mmap.mmap:
    """
    Memory‑maps the given file in read‑only mode.

    Parameters
    ----------
    file_path: str
        Path to the file to be memory‑mapped.

    Returns
    -------
    mmap.mmap
        A mmap object representing the file contents.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    PermissionError
        If the file cannot be opened for reading.
    RuntimeError
        If the underlying ``mmap`` call fails.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        fd = os.open(file_path, os.O_RDONLY)
    except OSError as exc:
        raise PermissionError(f"Unable to open file for reading: {file_path}") from exc

    try:
        size = os.fstat(fd).st_size
        if size == 0:
            # Empty files cannot be memory‑mapped; return a zero‑length mmap instead.
            return mmap.mmap(-1, 0, access=mmap.ACCESS_READ)

        # mmap.mmap may raise OSError for various platform‑specific reasons.
        try:
            mm = mmap.mmap(fd, length=0, access=mmap.ACCESS_READ)
        except OSError as exc:
            raise RuntimeError(f"mmap failed for {file_path}") from exc
        return mm
    finally:
        os.close(fd)


def unmap_file(mm: mmap.mmap) -> None:
    """
    Safely closes a previously created mmap object.

    Parameters
    ----------
    mm: mmap.mmap
        The mmap object to close.
    """
    try:
        mm.close()
    except Exception as exc:
        # In practice ``close`` rarely raises, but we guard against it to keep the API robust.
        raise RuntimeError("Failed to close mmap object") from exc


if __name__ == "__main__":
    # Self‑test: create a temporary file, write known data, map it, verify content,
    # then unmap and ensure cleanup.
    import tempfile

    test_content = b"The quick brown fox jumps over the lazy dog."

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(test_content)
        tmp.flush()

    try:
        # Map the file and verify content.
        mm = map_file_readonly(tmp_path)
        if mm[:] != test_content:
            raise AssertionError("Mapped content does not match original data")
        # Ensure the mmap object reports the correct size.
        if len(mm) != len(test_content):
            raise AssertionError("Mapped length is incorrect")
        # Unmap and verify that further access raises a ValueError.
        unmap_file(mm)
        try:
            _ = mm[:]
            raise AssertionError("Accessing unmapped memory should have failed")
        except ValueError:
            # Expected path: the mmap is closed.
            pass
    finally:
        # Clean up the temporary file.
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    # If we reach this point without raising, the test succeeded.
    sys.exit(0)