import mmap
import os
import sys
import tempfile


def safe_mmap_file(filepath: str, access: int = mmap.ACCESS_READ) -> memoryview:
    """
    Memory-map a file safely.

    Parameters
    ----------
    filepath : str
        Path to the file to be memory-mapped.
    access : int, optional
        mmap access flag (default is mmap.ACCESS_READ).

    Returns
    -------
    memoryview
        A read‑only memoryview of the file's contents.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    PermissionError
        If the file cannot be opened with the requested access.
    OSError
        For other OS‑level errors, such as mapping failures.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    # Open the file descriptor with appropriate mode
    # For read access we open in binary read mode.
    mode = "rb" if access in (mmap.ACCESS_READ, mmap.ACCESS_COPY) else "r+b"
    try:
        with open(filepath, mode) as f:
            fileno = f.fileno()
            file_size = os.fstat(fileno).st_size
            if file_size == 0:
                # mmap cannot map empty files; return an empty memoryview instead.
                return memoryview(b"")

            # mmap may raise OSError if mapping fails.
            mm = mmap.mmap(fileno, length=0, access=access)
            # Wrap the mmap object in a memoryview for easier slicing and to ensure
            # the underlying mmap stays alive as long as the view exists.
            view = memoryview(mm)
            # Keep a reference to the mmap inside the view's obj attribute to
            # prevent premature finalization.
            view.obj = mm  # type: ignore[attr-defined]
            return view
    except OSError as e:
        raise OSError(f"Failed to memory-map file '{filepath}': {e}") from e


if __name__ == "__main__":
    # Self‑test: create a temporary file, write known data, map it, and verify contents.
    test_data = b"The quick brown fox jumps over the lazy dog."
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(test_data)
        tmp.flush()

    try:
        mv = safe_mmap_file(tmp_path)
        if bytes(mv) != test_data:
            raise AssertionError("Mapped data does not match original data.")
        # Test empty file handling
        empty_path = tmp_path + "_empty"
        open(empty_path, "wb").close()
        empty_mv = safe_mmap_file(empty_path)
        if len(empty_mv) != 0:
            raise AssertionError("Empty file mapping should produce zero-length view.")
        # Clean up
        mv.release()  # type: ignore[attr-defined]
        empty_mv.release()  # type: ignore[attr-defined]
    finally:
        # Ensure temporary files are removed even if the test fails.
        for p in (tmp_path, empty_path):
            try:
                os.remove(p)
            except OSError:
                pass

    # If we reach this point, all tests passed.
    sys.exit(0)