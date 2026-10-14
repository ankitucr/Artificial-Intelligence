import mmap
import os
import tempfile


def safe_mmap(file_path, length=0, access=mmap.ACCESS_READ):
    """
    Safely memory‑map a file.

    Parameters
    ----------
    file_path : str
        Path to the file to be memory‑mapped.
    length : int, optional
        Number of bytes to map. If 0 (default) the entire file is mapped.
    access : int, optional
        mmap access mode, e.g. mmap.ACCESS_READ, mmap.ACCESS_WRITE,
        or mmap.ACCESS_COPY.

    Returns
    -------
    mmap.mmap
        The mmap object representing the mapped region.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    OSError
        If the mapping operation fails.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        fd = os.open(file_path, os.O_RDONLY if access == mmap.ACCESS_READ else os.O_RDWR)
        try:
            # Determine the mapping size
            if length == 0:
                file_size = os.fstat(fd).st_size
                map_len = file_size
            else:
                map_len = length

            # mmap may raise OSError if mapping fails; we surface that directly.
            mm = mmap.mmap(fd, map_len, access=access)
            return mm
        finally:
            os.close(fd)
    except OSError as exc:
        raise OSError(f"Failed to memory‑map file {file_path!r}: {exc}") from exc


if __name__ == "__main__":
    # Self‑test: create a temporary file, write data, map it, and verify contents.
    test_data = b"The quick brown fox jumps over the lazy dog."
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf.write(test_data)
        tf_path = tf.name

    try:
        mm = safe_mmap(tf_path)
        try:
            # Verify that the mapped data matches the original.
            if mm[:] != test_data:
                raise AssertionError("Mapped data does not match original data")
        finally:
            mm.close()
    finally:
        os.unlink(tf_path)