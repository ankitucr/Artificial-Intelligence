# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import os
import mmap
import errno
import tempfile


def safe_mmap(file_path, access=mmap.ACCESS_READ, offset=0, length=0):
    """
    Safely memory-maps a file.

    Parameters
    ----------
    file_path : str
        Path to the file to be memory-mapped.
    access : int, optional
        mmap access mode (default: mmap.ACCESS_READ).
    offset : int, optional
        Offset within the file where the mapping starts (default: 0).
    length : int, optional
        Number of bytes to map. If 0, maps the entire file from ``offset`` (default).

    Returns
    -------
    mmap.mmap
        The memory-mapped object.

    Raises
    ------
    FileNotFoundError
        If ``file_path`` does not exist.
    PermissionError
        If the file cannot be opened with the required permissions.
    OSError
        For any other OS-related errors.
    ValueError
        If the provided arguments are invalid.
    """
    if not isinstance(file_path, (str, bytes, os.PathLike)):
        raise ValueError("file_path must be a string, bytes, or os.PathLike object")

    if not os.path.isfile(file_path):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), file_path)

    # Determine the appropriate mode for opening the file based on access
    if access == mmap.ACCESS_READ:
        open_mode = "rb"
    elif access in (mmap.ACCESS_WRITE, mmap.ACCESS_COPY):
        open_mode = "r+b"
    else:
        raise ValueError(f"Unsupported mmap access flag: {access}")

    try:
        with open(file_path, open_mode) as f:
            # Resolve the mapping length
            if length == 0:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                length = file_size - offset
                if length < 0:
                    raise ValueError("Offset exceeds file size")
                f.seek(offset, os.SEEK_SET)

            # Ensure length is non-negative
            if length < 0:
                raise ValueError("Length must be non-negative")

            # Perform the actual memory mapping
            mm = mmap.mmap(f.fileno(), length, access=access, offset=offset)
            # Note: The file descriptor is still valid while ``mm`` is alive.
            return mm

    except OSError as e:
        # Re‑raise with a clearer message while preserving the original traceback
        raise OSError(f"Failed to memory‑map '{file_path}': {e.strerror}") from e


if __name__ == "__main__":
    # Test 1: Successful mapping of a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Hello, world!")
        tmp_path = tmp.name

    try:
        mm = safe_mmap(tmp_path)
        try:
            if mm[:].tobytes() != b"Hello, world!":
                raise AssertionError("Content mismatch after memory mapping")
        finally:
            mm.close()
    finally:
        os.unlink(tmp_path)

    # Test 2: Attempt to map a non‑existent file should raise FileNotFoundError
    non_existent = "/tmp/this_file_does_not_exist_12345"
    try:
        safe_mmap(non_existent)
        raise AssertionError("Expected FileNotFoundError was not raised")
    except FileNotFoundError:
        pass

    # Test 3: Attempt to map with an invalid offset should raise ValueError
    with tempfile.NamedTemporaryFile(delete=False) as tmp2:
        tmp2.write(b"abc")
        tmp2_path = tmp2.name

    try:
        try:
            safe_mmap(tmp2_path, offset=10)  # offset beyond file size
            raise AssertionError("Expected ValueError for offset beyond file size")
        except ValueError:
            pass
    finally:
        os.unlink(tmp2_path)

    print("All safe_mmap tests passed.")