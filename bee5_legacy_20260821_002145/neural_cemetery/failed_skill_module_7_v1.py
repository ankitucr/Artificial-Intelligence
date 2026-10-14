# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import mmap
import os
import tempfile
from typing import Optional


def safe_mmap(file_path: str, access: int = mmap.ACCESS_READ) -> mmap.mmap:
    """
    Safely memory‑map a file and raise a clear exception if mapping fails.

    Parameters
    ----------
    file_path: str
        Path to the file to be memory‑mapped.
    access: int, optional
        mmap access flag (default: mmap.ACCESS_READ).

    Returns
    -------
    mmap.mmap
        A memory‑mapped object.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    PermissionError
        If the file cannot be opened with the requested access.
    OSError
        For other OS‑level errors, including mapping failures.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        # Open the file with the appropriate mode based on requested access
        if access == mmap.ACCESS_READ:
            mode = "rb"
        elif access == mmap.ACCESS_WRITE:
            mode = "r+b"
        elif access == mmap.ACCESS_COPY:
            mode = "rb"
        else:
            raise ValueError(f"Unsupported mmap access mode: {access}")

        with open(file_path, mode) as f:
            # Determine the length to map; for zero‑length files mmap fails on many platforms
            size = os.fstat(f.fileno()).st_size
            if size == 0:
                raise OSError("Cannot mmap an empty file")
            # Perform the memory mapping
            return mmap.mmap(f.fileno(), length=0, access=access)
    except OSError as e:
        raise OSError(f"Failed to mmap file '{file_path}': {e}") from e


def read_mapped_file(file_path: str, encoding: str = "utf-8") -> str:
    """
    Convenience wrapper that memory‑maps a file, reads its contents, and closes the mapping.

    Parameters
    ----------
    file_path: str
        Path to the file to read.
    encoding: str, optional
        Text encoding to decode the bytes (default: "utf-8").

    Returns
    -------
    str
        The file's text content.
    """
    mm = safe_mmap(file_path, access=mmap.ACCESS_READ)
    try:
        data = mm[:]
        return data.decode(encoding)
    finally:
        mm.close()


def write_via_mmap(file_path: str, data: bytes) -> None:
    """
    Write data to a file using a memory‑mapped region.

    Parameters
    ----------
    file_path: str
        Path to the file to be created or overwritten.
    data: bytes
        Data to write.

    Raises
    ------
    ValueError
        If ``data`` is empty (mmap cannot map zero‑length files).
    """
    if not data:
        raise ValueError("Cannot mmap an empty buffer")
    # Ensure the file exists and has the correct size
    with open(file_path, "wb") as f:
        f.truncate(len(data))

    # Map and write
    with open(file_path, "r+b") as f:
        mm = mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_WRITE)
        try:
            mm[:] = data
        finally:
            mm.flush()
            mm.close()


if __name__ == "__main__":
    # Self‑test: create a temporary file, write via mmap, read back, and verify content.
    test_content = b"Hello, mmap world!"
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = os.path.join(tmpdir, "testfile.bin")

        # Write using mmap
        write_via_mmap(test_path, test_content)

        # Read using the wrapper
        read_back = read_mapped_file(test_path, encoding="utf-8")
        if read_back != test_content.decode("utf-8"):
            raise AssertionError("Read content does not match written content")

        # Directly test safe_mmap for read access
        mm = safe_mmap(test_path, access=mmap.ACCESS_READ)
        try:
            if mm[:].decode("utf-8") != "Hello, mmap world!":
                raise AssertionError("safe_mmap read mismatch")
        finally:
            mm.close()

    # If we reach this point, all tests passed.
    print("All self‑tests passed.")