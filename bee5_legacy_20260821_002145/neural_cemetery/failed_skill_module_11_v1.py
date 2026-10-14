# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def allocate_memory(size: int) -> bytearray:
    """
    Allocate a block of memory of the given size.

    This function mimics a low‑level memory allocation that would
    otherwise be performed by system calls in C/C++.  It raises a
    ``MemoryError`` if the allocation fails (e.g., if ``size`` is
    negative or excessively large for the interpreter to handle).

    Parameters
    ----------
    size: int
        Number of bytes to allocate. Must be non‑negative.

    Returns
    -------
    bytearray
        A mutable buffer of ``size`` zero‑initialized bytes.

    Raises
    ------
    ValueError
        If ``size`` is negative.
    MemoryError
        If the allocation cannot be satisfied.
    """
    if size < 0:
        raise ValueError("size must be non‑negative")
    try:
        return bytearray(size)
    except Exception as exc:
        raise MemoryError(f"Failed to allocate {size} bytes") from exc


if __name__ == "__main__":
    # Basic sanity checks
    # 1. Allocate a small buffer
    buf = allocate_memory(10)
    if len(buf) != 10:
        raise AssertionError("Allocated buffer has incorrect size")
    # 2. Ensure buffer is zero‑initialized
    if any(b != 0 for b in buf):
        raise AssertionError("Buffer not zero‑initialized")
    # 3. Test that negative size raises ValueError
    try:
        allocate_memory(-5)
        raise AssertionError("Negative size did not raise ValueError")
    except ValueError:
        pass
    # 4. Test that extremely large allocation raises MemoryError (platform dependent)
    try:
        allocate_memory(10**10)  # Adjust if this size is feasible on the test machine
        raise AssertionError("Extremely large allocation did not raise MemoryError")
    except MemoryError:
        pass

    # If we reach this point, all tests passed
    print("All allocate_memory tests passed.")