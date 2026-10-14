# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import os
import mmap
import errno


def safe_mmap(file_path: str, length: int, access: int = mmap.ACCESS_WRITE) -> mmap.mmap:
    """
    Safely memory‑map a file, creating it if necessary and ensuring it is at least ``length`` bytes.
    Returns the mmap object. Raises OSError on failure.

    Parameters
    ----------
    file_path: str
        Path to the file to be memory‑mapped.
    length: int
        Desired size of the mapping in bytes. The file will be truncated or extended to this size.
    access: int, optional
        mmap access flag (e.g., mmap.ACCESS_READ, mmap.ACCESS_WRITE, mmap.ACCESS_COPY).

    Returns
    -------
    mmap.mmap
        The memory‑mapped region.
    """
    if length < 0:
        raise ValueError("length must be non‑negative")

    # Ensure directory exists
    dir_name = os.path.dirname(file_path) or "."
    os.makedirs(dir_name, exist_ok=True)

    # Open the file, creating it if needed
    flags = os.O_RDWR | os.O_CREAT
    mode = 0o666  # default rw permissions, modified by umask
    fd = None
    try:
        fd = os.open(file_path, flags, mode)
        # Resize file to required length
        current_size = os.fstat(fd).st_size
        if current_size < length:
            # Extend file
            os.lseek(fd, length - 1, os.SEEK_SET)
            os.write(fd, b'\0')
        elif current_size > length:
            # Truncate file
            os.ftruncate(fd, length)

        # Memory‑map the file
        # mmap.mmap expects a file descriptor; we must keep it open until the mmap is closed
        mm = mmap.mmap(fd, length, access=access)
        return mm
    except OSError as e:
        # Provide a clearer error message while preserving the original exception details
        raise OSError(f"Failed to memory‑map '{file_path}' (length={length}): {e.strerror}") from e
    finally:
        if fd is not None:
            os.close(fd)


if __name__ == "__main__":
    # Self‑test for safe_mmap
    test_path = "tmp_test_mmap.bin"
    test_len = 1024

    # Clean up any previous test file
    try:
        os.remove(test_path)
    except FileNotFoundError:
        pass

    # Create mapping, write data, verify read back
    mm = safe_mmap(test_path, test_len, access=mmap.ACCESS_WRITE)
    try:
        sample = b"hello world"
        mm[:len(sample)] = sample
        mm.flush()

        # Re‑open to verify persistence
        mm2 = safe_mmap(test_path, test_len, access=mmap.ACCESS_READ)
        try:
            read_back = mm2[:len(sample)]
            if read_back != sample:
                raise AssertionError("Data mismatch after mmap write/read")
        finally:
            mm2.close()
    finally:
        mm.close()

    # Verify file size
    actual_size = os.path.getsize(test_path)
    if actual_size != test_len:
        raise AssertionError(f"File size {actual_size} does not match expected {test_len}")

    # Clean up test file
    os.remove(test_path)

    # If we reach here, all checks passed
    print("safe_mmap self‑test passed")