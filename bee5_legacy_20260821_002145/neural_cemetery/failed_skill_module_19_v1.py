# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import mmap
import os
import tempfile
from typing import Optional


def safe_mmap(
    file_path: str,
    length: int = 0,
    access: int = mmap.ACCESS_READ,
    *,
    offset: int = 0,
) -> mmap.mmap:
    """
    Safely memory‑map a file.

    Parameters
    ----------
    file_path : str
        Path to the file to be memory‑mapped.
    length : int, optional
        Number of bytes to map. ``0`` maps the entire file.
    access : int, optional
        mmap access flag (e.g., ``mmap.ACCESS_READ`` or ``mmap.ACCESS_WRITE``).
    offset : int, optional
        Offset in the file where the mapping starts.

    Returns
    -------
    mmap.mmap
        The mmap object.

    Raises
    ------
    FileNotFoundError
        If ``file_path`` does not exist.
    ValueError
        If ``offset`` is negative or not a multiple of the system's allocation granularity.
    OSError
        For any underlying OS error during mapping.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path!r}")

    if offset < 0:
        raise ValueError("offset must be non‑negative")

    # mmap requires offset to be a multiple of the allocation granularity
    granularity = mmap.ALLOCATIONGRANULARITY
    if offset % granularity != 0:
        raise ValueError(
            f"offset must be a multiple of allocation granularity ({granularity})"
        )

    # Open the file with appropriate mode based on requested access
    if access == mmap.ACCESS_WRITE:
        mode = "r+b"
    elif access == mmap.ACCESS_COPY:
        mode = "r+b"
    else:  # ACCESS_READ or default
        mode = "rb"

    try:
        with open(file_path, mode) as f:
            # Determine mapping size
            if length == 0:
                # Map to the end of file
                f.seek(0, os.SEEK_END)
                mapping_len = f.tell() - offset
                if mapping_len < 0:
                    raise ValueError(
                        "offset exceeds file size; cannot map beyond EOF"
                    )
            else:
                mapping_len = length

            # Ensure we don't map beyond EOF for read‑only maps
            if access != mmap.ACCESS_WRITE and mapping_len + offset > os.path.getsize(
                file_path
            ):
                raise ValueError(
                    "Requested mapping exceeds file size for read‑only access"
                )

            # mmap expects the file descriptor, not the file object
            fd = f.fileno()
            return mmap.mmap(fd, mapping_len, access=access, offset=offset)
    except OSError as e:
        raise OSError(f"Failed to memory‑map {file_path!r}: {e}") from e


def _test_safe_mmap() -> None:
    # Create a temporary file with known contents
    data = b"The quick brown fox jumps over the lazy dog"
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_name = tmp.name
        tmp.write(data)
        tmp.flush()

    try:
        # Read‑only mapping of the entire file
        mm = safe_mmap(tmp_name, access=mmap.ACCESS_READ)
        assert mm[:] == data, "Read‑only mmap data mismatch"
        mm.close()

        # Writeable mapping, modify a slice, then verify the file changed
        mm_w = safe_mmap(tmp_name, access=mmap.ACCESS_WRITE)
        mm_w[:4] = b"That"
        mm_w.flush()
        mm_w.close()

        with open(tmp_name, "rb") as f:
            modified = f.read()
        assert modified.startswith(b"That"), "Writeable mmap did not modify file"

        # Mapping with explicit length and offset
        offset = 10
        length = 5
        mm_slice = safe_mmap(tmp_name, length=length, offset=offset, access=mmap.ACCESS_READ)
        expected_slice = data[offset : offset + length]
        assert mm_slice[:] == expected_slice, "Offset/length mmap slice mismatch"
        mm_slice.close()
    finally:
        os.unlink(tmp_name)


if __name__ == "__main__":
    try:
        _test_safe_mmap()
        print("All safe_mmap tests passed.")
    except Exception as exc:
        print(f"Test failed: {exc}")
        raise  # Re‑raise to produce a non‑zero exit code.