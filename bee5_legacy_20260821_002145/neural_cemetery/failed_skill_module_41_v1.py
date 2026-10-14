# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import mmap
import os
import tempfile


def map_file(path: str) -> bytes:
    """
    Memory‑maps the file at *path* in read‑only mode and returns its contents as bytes.

    The function opens the file, creates a read‑only mmap, reads all data,
    closes the mmap and file, and returns the bytes.  It raises appropriate
    exceptions if the file cannot be opened or memory‑mapped.
    """
    if not isinstance(path, (str, bytes, os.PathLike)):
        raise TypeError("path must be a string, bytes, or os.PathLike")
    file_size = os.path.getsize(path)
    if file_size == 0:
        return b""
    with open(path, "rb") as f:
        # mmap.ACCESS_READ creates a read‑only mapping.
        with mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ) as mm:
            return mm[:]


if __name__ == "__main__":
    # Self‑test: write known data to a temporary file, map it, and verify.
    test_data = b"The quick brown fox jumps over the lazy dog"
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(test_data)
        tmp.flush()
    try:
        result = map_file(tmp_path)
        if result != test_data:
            raise AssertionError("Mapped data does not match original")
        # Test empty file handling
        empty_path = tmp_path + "_empty"
        open(empty_path, "wb").close()
        empty_result = map_file(empty_path)
        if empty_result != b"":
            raise AssertionError("Empty file should return empty bytes")
    finally:
        # Clean up temporary files
        for p in (tmp_path, empty_path):
            try:
                os.remove(p)
            except OSError:
                pass
    print("All tests passed.")