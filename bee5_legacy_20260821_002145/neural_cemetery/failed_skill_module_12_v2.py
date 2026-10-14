# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import mmap
import os
import tempfile
from typing import Optional


def safe_mmap(file_path: str, access: int = mmap.ACCESS_READ) -> mmap.mmap:
    """
    Safely memory-map a file.

    Args:
        file_path: Path to the file to be memory-mapped.
        access: mmap access flag (default is read-only).

    Returns:
        An mmap.mmap object representing the mapped file.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty.
        OSError: For other OS-related errors.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise ValueError(f"Cannot memory-map an empty file: {file_path}")

    fd = os.open(file_path, os.O_RDONLY)
    try:
        # mmap may raise OSError; we let it propagate as it provides useful info.
        mm = mmap.mmap(fd, length=0, access=access)
        if mm is None:
            # This is highly unlikely in Python, but we guard against it.
            raise OSError("mmap returned None, indicating failure to map")
        return mm
    finally:
        os.close(fd)


def safe_unmap(mm: mmap.mmap) -> None:
    """
    Safely close a memory-mapped object.

    Args:
        mm: The mmap.mmap object to close.
    """
    if mm is not None:
        mm.close()


if __name__ == "__main__":
    # Self-test: create a temporary file, write known data, map it, verify contents,
    # then unmap and ensure no exceptions are raised.
    test_data = b"The quick brown fox jumps over the lazy dog"
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf_name = tf.name
        tf.write(test_data)
        tf.flush()

    try:
        # Map the file
        mapped = safe_mmap(tf_name)
        # Verify the content matches
        if mapped[:] != test_data:
            raise AssertionError("Mapped data does not match original data")
        # Unmap
        safe_unmap(mapped)

        # Edge cases
        # 1. Empty file should raise ValueError
        empty_path = tf_name + "_empty"
        with open(empty_path, "wb"):
            pass  # create empty file
        try:
            safe_mmap(empty_path)
            raise AssertionError("Mapping an empty file should have raised ValueError")
        except ValueError:
            pass  # Expected

        # 2. Nonexistent file should raise FileNotFoundError
        try:
            safe_mmap(tf_name + "_does_not_exist")
            raise AssertionError("Mapping a nonexistent file should have raised FileNotFoundError")
        except FileNotFoundError:
            pass  # Expected

    finally:
        # Clean up temporary files
        os.unlink(tf_name)
        if os.path.exists(empty_path):
            os.unlink(empty_path)