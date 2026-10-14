import mmap
import os
import sys
from typing import Optional


def safe_mmap_read(filepath: str, length: Optional[int] = None) -> mmap.mmap:
    """
    Safely memory‑maps a file for reading.

    Args:
        filepath: Path to the file to be memory‑mapped.
        length: Number of bytes to map. If None, maps the whole file.

    Returns:
        An mmap.mmap object opened in read‑only mode.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be opened for reading.
        ValueError: If length is negative or exceeds the file size.
        OSError: For any other OS‑level mapping errors.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    file_size = os.path.getsize(filepath)
    if length is None:
        length = file_size
    elif length < 0:
        raise ValueError("length must be non‑negative")
    elif length > file_size:
        raise ValueError("length exceeds file size")

    # Open the file descriptor in read‑only mode
    fd = os.open(filepath, os.O_RDONLY)
    try:
        # mmap with PROT_READ and MAP_PRIVATE ensures a private, read‑only view
        mm = mmap.mmap(fd, length, access=mmap.ACCESS_READ)
        return mm
    except Exception as e:
        raise OSError(f"Failed to memory‑map {filepath}: {e}") from e
    finally:
        os.close(fd)


def safe_mmap_write(filepath: str, data: bytes) -> None:
    """
    Safely creates a file and writes data to it using memory‑mapping.

    Args:
        filepath: Path to the file to be created/overwritten.
        data: Bytes to write.

    Raises:
        PermissionError: If the file cannot be created or written.
        OSError: For any other OS‑level errors.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

    # Open (or create) the file with read/write permissions
    fd = os.open(filepath, os.O_RDWR | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        # Resize the file to the required length
        os.ftruncate(fd, len(data))

        # mmap with read/write access
        mm = mmap.mmap(fd, len(data), access=mmap.ACCESS_WRITE)
        try:
            mm[:] = data
            mm.flush()
        finally:
            mm.close()
    except Exception as e:
        raise OSError(f"Failed to write via mmap to {filepath}: {e}") from e
    finally:
        os.close(fd)


if __name__ == "__main__":
    # Self‑test: write data, read it back, and verify integrity.
    test_path = "temp_mmap_test.bin"
    test_data = b"The quick brown fox jumps over the lazy dog."

    # Write using mmap
    safe_mmap_write(test_path, test_data)

    # Read back using mmap
    mm = safe_mmap_read(test_path)
    try:
        read_back = mm[:]
    finally:
        mm.close()

    # Clean up the test file
    try:
        os.remove(test_path)
    except Exception:
        pass

    if read_back != test_data:
        sys.exit(1)  # Signal failure
    # If we reach this point, the test succeeded.
    sys.exit(0)