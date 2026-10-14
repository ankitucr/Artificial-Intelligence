# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import os
import mmap
import tempfile
import unittest


def safe_mmap(file_path):
    """
    Memory-maps the given file and returns its contents as bytes.

    This function opens the file in read‑only binary mode, creates a read‑only
    mmap, and returns a copy of the mapped data. All resources are properly
    closed even if an exception occurs.

    Args:
        file_path (str): Path to the file to be memory‑mapped.

    Returns:
        bytes: The full contents of the file.

    Raises:
        OSError: If the file cannot be opened or memory‑mapped.
    """
    if not isinstance(file_path, (str, bytes, os.PathLike)):
        raise TypeError("file_path must be a path-like object")
    fd = None
    mm = None
    try:
        fd = os.open(file_path, os.O_RDONLY)
        file_size = os.fstat(fd).st_size
        if file_size == 0:
            return b""
        mm = mmap.mmap(fd, length=0, access=mmap.ACCESS_READ)
        # Return a copy to avoid keeping the mmap open for the caller.
        data = mm[:]
        return data
    finally:
        if mm is not None:
            try:
                mm.close()
            except Exception:
                pass
        if fd is not None:
            try:
                os.close(fd)
            except Exception:
                pass


if __name__ == "__main__":
    class TestSafeMmap(unittest.TestCase):
        def test_empty_file(self):
            with tempfile.NamedTemporaryFile(delete=False) as tf:
                path = tf.name
            try:
                self.assertEqual(safe_mmap(path), b"")
            finally:
                os.unlink(path)

        def test_small_content(self):
            content = b"Hello, safe_mmap!"
            with tempfile.NamedTemporaryFile(delete=False) as tf:
                tf.write(content)
                tf.flush()
                path = tf.name
            try:
                self.assertEqual(safe_mmap(path), content)
            finally:
                os.unlink(path)

        def test_large_content(self):
            content = os.urandom(5 * 1024 * 1024)  # 5 MB
            with tempfile.NamedTemporaryFile(delete=False) as tf:
                tf.write(content)
                tf.flush()
                path = tf.name
            try:
                self.assertEqual(safe_mmap(path), content)
            finally:
                os.unlink(path)

        def test_invalid_path(self):
            with self.assertRaises(OSError):
                safe_mmap("/nonexistent/path/does_not_exist.txt")

        def test_invalid_type(self):
            with self.assertRaises(TypeError):
                safe_mmap(12345)

    unittest.main()