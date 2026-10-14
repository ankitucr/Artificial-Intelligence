# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import mmap
import os
import sys
from typing import Optional


def safe_mmap_file(filepath: str, access: int = mmap.ACCESS_READ) -> mmap.mmap:
    """
    Memory‑map the given file safely.

    Parameters
    ----------
    filepath: str
        Path to the file to be memory‑mapped.
    access: int, optional
        mmap access mode (default ``mmap.ACCESS_READ``). Use
        ``mmap.ACCESS_WRITE`` or ``mmap.ACCESS_COPY`` as needed.

    Returns
    -------
    mmap.mmap
        A memory‑mapped object representing the file contents.

    Raises
    ------
    FileNotFoundError
        If ``filepath`` does not exist.
    PermissionError
        If the file cannot be opened with the required permissions.
    OSError
        For any other OS‑level error, including failure to map the file.
    """
    if not isinstance(filepath, str):
        raise TypeError("filepath must be a string")
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    try:
        # Open the file descriptor with the appropriate flags based on the requested access.
        if access == mmap.ACCESS_WRITE:
            mode = "r+b"
        elif access == mmap.ACCESS_COPY:
            mode = "r+b"
        else:  # ACCESS_READ or any other value defaults to read‑only.
            mode = "rb"

        fd = os.open(filepath, os.O_RDONLY if mode == "rb" else os.O_RDWR)
        try:
            # Determine the size of the file.
            file_size = os.fstat(fd).st_size
            if file_size == 0:
                # mmap of an empty file is undefined on many platforms; raise a clear error.
                raise ValueError("Cannot memory‑map an empty file")

            # Perform the mmap operation.
            mm = mmap.mmap(fd, length=0, access=access)
            if mm is None:
                # This mirrors the C++ MAP_FAILED check.
                raise OSError("mmap returned None (MAP_FAILED equivalent)")

            return mm
        finally:
            os.close(fd)
    except Exception as exc:
        # Re‑raise with a consistent message while preserving the original traceback.
        raise OSError(f"Failed to memory‑map file '{filepath}': {exc}") from exc


def _test_safe_mmap_file() -> None:
    # Create a temporary file with known contents.
    import tempfile

    content = b"The quick brown fox jumps over the lazy dog."
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_name = tmp.name
        tmp.write(content)
        tmp.flush()

    try:
        # Test read‑only mapping.
        mm = safe_mmap_file(tmp_name, access=mmap.ACCESS_READ)
        assert mm[: len(content)] == content, "Read‑only mmap content mismatch"
        mm.close()

        # Test write mapping (modify and verify).
        mm = safe_mmap_file(tmp_name, access=mmap.ACCESS_WRITE)
        new_slice = b"slow"
        mm[10:14] = new_slice
        mm.flush()
        mm.close()

        # Verify the file on disk reflects the change.
        with open(tmp_name, "rb") as f:
            data = f.read()
        expected = content[:10] + new_slice + content[14:]
        assert data == expected, "Write mmap did not persist changes"

        # Test mapping an empty file raises ValueError.
        empty_path = tmp_name + "_empty"
        open(empty_path, "wb").close()
        try:
            safe_mmap_file(empty_path)
            raise AssertionError("Mapping empty file should have raised ValueError")
        except ValueError:
            pass
        finally:
            os.remove(empty_path)

    finally:
        os.remove(tmp_name)


if __name__ == "__main__":
    try:
        _test_safe_mmap_file()
        print("All safe_mmap_file tests passed.")
    except Exception as e:
        print(f"Test failure: {e}", file=sys.stderr)
        sys.exit(1)