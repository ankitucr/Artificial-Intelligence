# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

import itertools

def chunked(iterable, size):
    """Yield successive chunks of length `size` from `iterable`.

    Args:
        iterable: Any iterable source of items.
        size (int): Positive integer size of each chunk.

    Yields:
        List containing up to `size` items from the iterable.

    Raises:
        ValueError: If `size` is not a positive integer.
    """
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, size))
        if not chunk:
            break
        yield chunk

if __name__ == "__main__":
    # Basic functionality test
    data = list(range(10))
    expected = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]
    result = list(chunked(data, 3))
    if result != expected:
        raise AssertionError(f"chunked list test failed: {result} != {expected}")

    # Test with a generator as input
    gen = (i * i for i in range(7))  # 0,1,4,9,16,25,36
    expected_gen = [[0, 1, 4], [9, 16, 25], [36]]
    result_gen = list(chunked(gen, 3))
    if result_gen != expected_gen:
        raise AssertionError(f"chunked generator test failed: {result_gen} != {expected_gen}")

    # Test that invalid size raises ValueError
    try:
        list(chunked(data, 0))
        raise AssertionError("chunked did not raise ValueError for size=0")
    except ValueError:
        pass

    try:
        list(chunked(data, -5))
        raise AssertionError("chunked did not raise ValueError for negative size")
    except ValueError:
        pass

    # If all tests pass, print a success message
    print("All chunked tests passed.")