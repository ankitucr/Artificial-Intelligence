# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import mmap
import os
import sys
from typing import Optional


def safe_mmap(file_path: str, access: int = mmap.ACCESS_READ) -> mmap.mmap:
    """
    Safely memory‑maps a file and raises a clear exception if the mapping fails.

    Parameters
    ----------
    file_path : str
        Path to the file to be memory‑mapped.
    access : int, optional
        mmap access mode (default: mmap.ACCESS_READ).

    Returns
    -------
    mmap.mmap
        The memory‑mapped file object.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    PermissionError
        If the file cannot be opened with the required permissions.
    OSError
        If the mmap operation fails for any other reason.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Open the file with appropriate mode based on requested access.
    mode = "rb" if access == mmap.ACCESS_READ else "r+b"
    try:
        with open(file_path, mode) as f:
            fileno = f.fileno()
            file_size = os.fstat(fileno).st_size
            if file_size == 0:
                raise OSError("Cannot mmap an empty file.")
            # mmap.mmap will raise an OSError if mapping fails.
            try:
                mm = mmap.mmap(fileno, length=0, access=access)
                return mm
            except OSError as e:
                raise OSError(f"mmap failed for {file_path!r}: {e}") from e
    except PermissionError as e:
        raise PermissionError(f"Permission denied when opening {file_path!r}: {e}") from e
    except OSError as e:
        raise OSError(f"Failed to open {file_path!r}: {e}") from e


def safe_unmap(mm: mmap.mmap) -> None:
    """
    Safely close a memory‑mapped object.

    Parameters
    ----------
    mm : mmap.mmap
        The memory‑mapped object to close.

    Raises
    ------
    ValueError
        If the mmap object is already closed.
    """
    if mm.closed:
        raise ValueError("mmap object is already closed.")
    mm.close()


if __name__ == "__main__":
    # Self‑test: create a temporary file, write data, map it, verify contents,
    # then unmap and ensure proper cleanup.

    import tempfile

    test_content = b"Hello, safe mmap!"

    # Create a temporary file with known content.
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_name = tmp.name
        tmp.write(test_content)
        tmp.flush()
        os.fsync(tmp.fileno())

    try:
        # Map the file and verify contents.
        mm = safe_mmap(tmp_name)
        try:
            read_back = mm[:]
            if read_back != test_content:
                raise AssertionError(
                    f"Mapped content mismatch: expected {test_content!r}, got {read_back!r}"
                )
        finally:
            # Ensure unmapping works and raises if double‑closed.
            safe_unmap(mm)
            try:
                safe_unmap(mm)
                raise AssertionError("safe_unmap did not raise on double close")
            except ValueError:
                pass  # Expected

        # Test handling of non‑existent file.
        try:
            safe_mmap("non_existent_file.xyz")
            raise AssertionError("safe_mmap did not raise FileNotFoundError for missing file")
        except FileNotFoundError:
            pass  # Expected

        # Test handling of empty file.
        with tempfile.NamedTemporaryFile(delete=False) as empty_tmp:
            empty_name = empty_tmp.name
        try:
            safe_mmap(empty_name)
            raise AssertionError("safe_mmap did not raise OSError for empty file")
        except OSError:
            pass  # Expected
        finally:
            os.unlink(empty_name)

    finally:
        os.unlink(tmp_name)

    print("All safe_mmap tests passed.")