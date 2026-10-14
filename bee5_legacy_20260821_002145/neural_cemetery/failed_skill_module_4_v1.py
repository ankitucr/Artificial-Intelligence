# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import mmap
import os
import tempfile
from contextlib import contextmanager


@contextmanager
def safe_mmap(file_path: str, access: int = mmap.ACCESS_WRITE) -> mmap.mmap:
    """
    Safely memory‑map the given file.

    This context manager opens ``file_path`` (creating it if it does not exist),
    ensures the file is at least one byte long, and maps it using ``mmap``.
    It raises ``OSError`` with a clear message if any step fails.

    Parameters
    ----------
    file_path: str
        Path to the file to be memory‑mapped.
    access: int, optional
        ``mmap`` access flag (default ``mmap.ACCESS_WRITE``).

    Yields
    ------
    mmap.mmap
        The memory‑mapped object. It is automatically closed when the context
        exits.

    Example
    -------
    >>> with safe_mmap('tmp.bin') as mm:
    ...     mm[:4] = b'test'
    """
    fd = None
    mm = None
    try:
        # Open the file descriptor; create if missing.
        flags = os.O_RDWR | os.O_CREAT
        fd = os.open(file_path, flags, 0o600)

        # Ensure the file is at least one byte; mmap cannot map an empty file.
        stat = os.fstat(fd)
        if stat.st_size == 0:
            os.write(fd, b'\x00')
        # Re‑stat after potential write.
        os.lseek(fd, 0, os.SEEK_SET)

        # Memory‑map the file.
        try:
            mm = mmap.mmap(fd, 0, access=access)
        except Exception as exc:
            raise OSError(f"Failed to mmap file '{file_path}': {exc}") from exc

        yield mm
    finally:
        if mm is not None:
            try:
                mm.flush()
                mm.close()
            except Exception:
                pass
        if fd is not None:
            try:
                os.close(fd)
            except Exception:
                pass


def _self_test():
    # Create a temporary file and map it.
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Write known content.
        with open(tmp_path, "wb") as f:
            f.write(b"HelloWorld")

        # Read and modify via safe_mmap.
        with safe_mmap(tmp_path, access=mmap.ACCESS_WRITE) as mm:
            # Verify initial content.
            if mm[:10] != b"HelloWorld":
                raise AssertionError("Initial mmap content mismatch")

            # Modify content.
            mm[0:5] = b"Bye!!"

        # Verify changes persisted.
        with open(tmp_path, "rb") as f:
            data = f.read()
            if data != b"Bye!!World":
                raise AssertionError(f"Persisted data mismatch: {data!r}")

        # Test mapping an empty file (should be auto‑expanded).
        empty_path = tmp_path + "_empty"
        open(empty_path, "wb").close()
        with safe_mmap(empty_path, access=mmap.ACCESS_WRITE) as mm:
            # After mapping, file should be at least 1 byte.
            if len(mm) == 0:
                raise AssertionError("Empty file mmap length is zero")
            # Write a byte and ensure it persists.
            mm[0] = 0x41  # 'A'
        with open(empty_path, "rb") as f:
            if f.read() != b"A":
                raise AssertionError("Empty file content not persisted")
    finally:
        # Clean up temporary files.
        for p in (tmp_path, empty_path):
            try:
                os.remove(p)
            except OSError:
                pass


if __name__ == "__main__":
    _self_test()
    print("All safe_mmap tests passed.")