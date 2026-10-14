# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import mmap
import os
import tempfile
from typing import Optional, Union


def safe_mmap(file_path: Union[str, bytes, os.PathLike]) -> Optional[memoryview]:
    """
    Safely memory‑map the given file in read‑only mode.

    Returns a memoryview of the file's contents, or ``None`` if the mapping
    fails for any reason (e.g. the file does not exist, permission denied,
    or the underlying mmap call raises an exception).

    The returned memoryview does not own the underlying ``mmap`` object;
    the caller should keep a reference to the ``mmap`` object if the
    memoryview is needed beyond the scope of this function. To simplify
    usage, this function returns the ``mmap`` object itself, which can be
    used as a bytes‑like object directly.

    Example
    -------
    >>> mm = safe_mmap("example.txt")
    >>> if mm is not None:
    ...     print(mm[:10])  # first 10 bytes
    """
    try:
        fd = os.open(file_path, os.O_RDONLY)
    except OSError:
        return None

    try:
        file_size = os.fstat(fd).st_size
        if file_size == 0:
            # mmap cannot map an empty file; treat as empty bytes
            return memoryview(b"")
        mm = mmap.mmap(fd, length=0, access=mmap.ACCESS_READ)
        return mm
    except Exception:
        return None
    finally:
        # The file descriptor can be closed after mmap; the mmap object
        # keeps the mapping alive.
        try:
            os.close(fd)
        except OSError:
            pass


def read_mapped_file(file_path: Union[str, bytes, os.PathLike]) -> Optional[bytes]:
    """
    Convenience wrapper that returns the full contents of a file using
    ``safe_mmap``. If mapping fails, ``None`` is returned.

    Parameters
    ----------
    file_path: path to the file to read.

    Returns
    -------
    bytes or None
    """
    mm = safe_mmap(file_path)
    if mm is None:
        return None
    try:
        # ``mm`` behaves like a bytes object; slice to get a copy.
        return mm[:]
    finally:
        # Explicitly close the mmap to release resources.
        try:
            mm.close()
        except Exception:
            pass


if __name__ == "__main__":
    # Self‑test: create a temporary file, write known data, read via the
    # memory‑mapping utilities, and verify the result.
    test_data = b"The quick brown fox jumps over the lazy dog"

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_name = tmp.name
        tmp.write(test_data)
        tmp.flush()

    try:
        # Test safe_mmap returns a mmap object with correct content
        mapped = safe_mmap(tmp_name)
        if mapped is None:
            raise RuntimeError("safe_mmap returned None for a valid file")
        if mapped[:] != test_data:
            raise AssertionError("Mapped content does not match original data")
        # Ensure we can close without error
        mapped.close()

        # Test read_mapped_file returns exact bytes
        read_back = read_mapped_file(tmp_name)
        if read_back != test_data:
            raise AssertionError("read_mapped_file returned incorrect data")
    finally:
        # Clean up the temporary file
        try:
            os.unlink(tmp_name)
        except OSError:
            pass

    # If we reach this point without exception, the test succeeded.
    print("All self‑tests passed.")