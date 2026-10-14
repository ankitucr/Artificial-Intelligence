# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import mmap
import os
import sys
import tempfile

def safe_mmap_read(file_path):
    """
    Safely memory-map the entire contents of a file and return it as bytes.
    This function ensures that the file is opened correctly, the mapping succeeds,
    and the resources are cleaned up properly.

    Parameters
    ----------
    file_path : str
        Path to the file to be memory-mapped.

    Returns
    -------
    bytes
        The contents of the file.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    PermissionError
        If the file cannot be opened due to insufficient permissions.
    OSError
        For other OS-related errors, including mapping failures.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Open the file in read-only binary mode
    with open(file_path, "rb") as f:
        # Determine the file size
        f.seek(0, os.SEEK_END)
        size = f.tell()
        if size == 0:
            return b""
        f.seek(0)

        # Memory-map the file
        try:
            with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
                # Return a copy of the bytes to detach from the mmap object
                return mm[:]
        except Exception as e:
            raise OSError(f"Failed to memory-map file {file_path}: {e}") from e

if __name__ == "__main__":
    # Self-test: create a temporary file, write known data, read via safe_mmap_read
    test_data = b"The quick brown fox jumps over the lazy dog"
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_name = tmp.name
        tmp.write(test_data)
        tmp.flush()
    try:
        read_data = safe_mmap_read(tmp_name)
        if read_data != test_data:
            raise AssertionError("Data mismatch between written and read content")
        # Test empty file handling
        empty_name = tmp_name + "_empty"
        open(empty_name, "wb").close()
        empty_data = safe_mmap_read(empty_name)
        if empty_data != b"":
            raise AssertionError("Empty file should return empty bytes")
    finally:
        # Clean up temporary files
        for path in [tmp_name, empty_name]:
            try:
                os.remove(path)
            except OSError:
                pass

    # If we reach this point, all tests passed
    sys.exit(0)