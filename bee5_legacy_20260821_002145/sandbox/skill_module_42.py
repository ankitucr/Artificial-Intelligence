import mmap
import os
import tempfile

def safe_mmap(file_path, length=0, access=mmap.ACCESS_READ):
    """
    Safely memory‑maps a file.

    Parameters
    ----------
    file_path : str
        Path to the file to be memory‑mapped.
    length : int, optional
        Number of bytes to map. If 0 (default), the entire file is mapped.
    access : int, optional
        mmap access flag (e.g., mmap.ACCESS_READ, mmap.ACCESS_WRITE).

    Returns
    -------
    mmap.mmap
        The memory‑mapped object.

    Raises
    ------
    FileNotFoundError
        If ``file_path`` does not exist.
    OSError
        If the underlying ``mmap`` call fails.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    fd = -1
    try:
        fd = os.open(file_path, os.O_RDONLY if access == mmap.ACCESS_READ else os.O_RDWR)
        file_size = os.fstat(fd).st_size

        # If length is zero, map the whole file.
        map_len = length if length > 0 else file_size

        # Guard against mapping zero bytes which mmap does not allow.
        if map_len == 0:
            raise ValueError("Cannot mmap an empty file or zero length.")

        # Perform the mapping.
        mm = mmap.mmap(fd, map_len, access=access)

        # Ensure the mapping succeeded.
        if mm is None:
            raise OSError("mmap returned None (unexpected).")
        return mm
    except OSError as e:
        raise OSError(f"Failed to memory‑map file '{file_path}': {e}") from e
    finally:
        if fd != -1:
            os.close(fd)


if __name__ == "__main__":
    # Self‑test: create a temporary file, write data, map it, and verify contents.
    test_data = b"The quick brown fox jumps over the lazy dog"
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_name = tmp.name
        tmp.write(test_data)
        tmp.flush()

    try:
        # Map the whole file.
        mm = safe_mmap(tmp_name)
        if mm[:len(test_data)] != test_data:
            raise AssertionError("Mapped data does not match original data (full map).")
        mm.close()

        # Map a subset of the file.
        subset_len = 20
        mm_subset = safe_mmap(tmp_name, length=subset_len)
        if mm_subset[:subset_len] != test_data[:subset_len]:
            raise AssertionError("Mapped subset does not match original data.")
        mm_subset.close()
    finally:
        os.unlink(tmp_name)  # Clean up the temporary file.