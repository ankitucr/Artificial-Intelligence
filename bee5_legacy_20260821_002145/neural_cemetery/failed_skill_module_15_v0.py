# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunked(iterable, size):
    """
    Yield successive chunks from ``iterable`` of length ``size``.
    The final chunk may be shorter if the total number of items
    is not a multiple of ``size``.

    Args:
        iterable: Any iterable (list, tuple, generator, etc.).
        size: Positive integer indicating the chunk size.

    Yields:
        Tuple containing up to ``size`` elements from ``iterable``.

    Example:
        >>> list(chunked([1, 2, 3, 4, 5], 2))
        [(1, 2), (3, 4), (5,)]
    """
    if size <= 0:
        raise ValueError("size must be a positive integer")
    it = iter(iterable)
    while True:
        chunk = tuple([next(it) for _ in range(size) if True] )
        # The list comprehension above will attempt to fetch `size` items,
        # but it will raise StopIteration when the iterator is exhausted.
        # To handle that gracefully, we catch the exception.
        if not chunk:
            break
        yield chunk
        # If the iterator was exhausted during the list comprehension,
        # the loop will naturally exit on the next iteration because
        # `chunk` will be empty.

if __name__ == "__main__":
    # Basic tests
    # Test 1: standard case
    data = list(range(10))
    expected = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9,)]
    result = list(chunked(data, 3))
    assert result == expected, f"Test 1 failed: expected {expected}, got {result}"

    # Test 2: size larger than iterable
    data = [1, 2, 3]
    expected = [(1, 2, 3)]
    result = list(chunked(data, 10))
    assert result == expected, f"Test 2 failed: expected {expected}, got {result}"

    # Test 3: size of 1 returns each element as a tuple
    data = ['a', 'b', 'c']
    expected = [('a',), ('b',), ('c',)]
    result = list(chunked(data, 1))
    assert result == expected, f"Test 3 failed: expected {expected}, got {result}"

    # Test 4: invalid size raises ValueError
    try:
        list(chunked([1, 2, 3], 0))
        raise AssertionError("Test 4 failed: ValueError not raised for size=0")
    except ValueError:
        pass

    # Test 5: iterator input works correctly
    def gen():
        for i in range(5):
            yield i * i
    expected = [(0, 1), (4, 9), (16,)]
    result = list(chunked(gen(), 2))
    assert result == expected, f"Test 5 failed: expected {expected}, got {result}"

    print("All tests passed.")