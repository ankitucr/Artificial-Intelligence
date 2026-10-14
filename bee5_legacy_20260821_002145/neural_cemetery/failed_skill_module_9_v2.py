# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import mmap
import os
import tempfile
from typing import Optional


def robust_mmap(
    fileno: int,
    length: int,
    prot: int = mmap.PROT_READ,
    flags: int = mmap.MAP_SHARED,
    offset: int = 0,
) -> mmap.mmap:
    """
    Create an mmap object with explicit error handling.

    Parameters
    ----------
    fileno : int
        File descriptor to map.
    length : int
        Number of bytes to map. Must be > 0.
    prot : int, optional
        Memory protection flags (default: mmap.PROT_READ).
    flags : int, optional
        Mapping flags (default: mmap.MAP_SHARED).
    offset : int, optional
        Offset in the file to start mapping (default: 0).

    Returns
    -------
    mmap.mmap
        The memory‑mapped object.

    Raises
    ------
    ValueError
        If ``length`` is non‑positive.
    OSError
        If the underlying ``mmap.mmap`` call fails.
    """
    if length <= 0:
        raise ValueError("length must be a positive integer")

    try:
        # mmap.mmap may raise OSError on failure (e.g., MAP_FAILED)
        mm = mmap.mmap(fileno, length, prot=prot, flags=flags, offset=offset)
        return mm
    except OSError as exc:
        # Re‑raise with a clearer message while preserving the original traceback.
        raise OSError(f"Failed to mmap file descriptor {fileno}: {exc}") from exc


def mmap_file_readonly(path: str) -> mmap.mmap:
    """
    Open *path* read‑only and memory‑map its entire contents.

    This is a convenience wrapper around :func:`robust_mmap` that handles
    opening the file and determining its size.

    Parameters
    ----------
    path : str
        Path to the file to be memory‑mapped.

    Returns
    -------
    mmap.mmap
        A read‑only mmap of the file's contents.

    Raises
    ------
    FileNotFoundError
        If *path* does not exist.
    OSError
        If the mapping operation fails.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No such file: {path}")

    size = os.path.getsize(path)
    if size == 0:
        raise ValueError("Cannot mmap an empty file")

    fd = os.open(path, os.O_RDONLY)
    try:
        return robust_mmap(fd, size, prot=mmap.PROT_READ, flags=mmap.MAP_PRIVATE)
    finally:
        os.close(fd)


if __name__ == "__main__":
    # Self‑test: create a temporary file, write data, mmap it and verify contents.
    test_data = b"The quick brown fox jumps over the lazy dog."

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_name = tmp.name
        tmp.write(test_data)
        tmp.flush()
        tmp_fd = tmp.fileno()

    try:
        # Verify robust_mmap directly
        mm_direct = robust_mmap(tmp_fd, len(test_data), prot=mmap.PROT_READ, flags=mmap.MAP_PRIVATE)
        if mm_direct[:] != test_data:
            raise AssertionError("robust_mmap content mismatch")
        mm_direct.close()

        # Verify mmap_file_readonly wrapper
        mm_wrapper = mmap_file_readonly(tmp_name)
        if mm_wrapper[:] != test_data:
            raise AssertionError("mmap_file_readonly content mismatch")
        mm_wrapper.close()
    finally:
        os.unlink(tmp_name)  # Clean up the temporary file

    # If we reach this point without raising, the test succeeded.
    print("All tests passed.")