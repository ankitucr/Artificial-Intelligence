# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import mmap
import os
import tempfile


def safe_mmap(file_path: str, length: int, access: int = mmap.ACCESS_WRITE) -> mmap.mmap:
    """
    Create a memory-mapped region for the given file.

    Args:
        file_path: Path to the file to be memory-mapped.
        length: Size of the mapping. The file will be extended if it is smaller.
        access: mmap access flag (default: mmap.ACCESS_WRITE).

    Returns:
        An mmap object representing the memory-mapped region.

    Raises:
        OSError: If the file cannot be opened or the mapping fails.
        ValueError: If length is negative.
    """
    if length < 0:
        raise ValueError("length must be non‑negative")

    # Ensure the file exists and has the required size
    fd = os.open(file_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        current_size = os.path.getsize(file_path)
        if current_size < length:
            # Extend the file to the required size
            os.lseek(fd, length - 1, os.SEEK_SET)
            os.write(fd, b'\x00')
        # Memory‑map the file
        return mmap.mmap(fd, length, access=access)
    finally:
        os.close(fd)


if __name__ == "__main__":
    # Self‑test for safe_mmap
    test_data = b"hello world"
    map_size = 1024  # larger than test_data

    with tempfile.NamedTemporaryFile(delete=False) as tf:
        temp_path = tf.name

    try:
        # Write initial data
        with open(temp_path, "wb") as f:
            f.write(test_data)

        # Create mmap
        mm = safe_mmap(temp_path, map_size, access=mmap.ACCESS_WRITE)

        # Verify existing content
        if mm[: len(test_data)] != test_data:
            raise AssertionError("Initial data mismatch in mmap")

        # Modify the mmap content
        new_data = b"goodbye"
        mm[: len(new_data)] = new_data

        # Flush changes to the underlying file
        mm.flush()

        # Verify changes are reflected in the file
        with open(temp_path, "rb") as f:
            file_content = f.read(len(new_data))
            if file_content != new_data:
                raise AssertionError("File content not updated after mmap write")

        # Clean up mmap
        mm.close()
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    print("safe_mmap self‑test passed")