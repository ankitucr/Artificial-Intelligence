# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def chunked(seq, size):
    """
    Split a sequence into consecutive chunks of given size.

    Args:
        seq: Any iterable (list, tuple, string, etc.).
        size: Positive integer chunk size.

    Returns:
        A list of chunks, where each chunk is of the same type as the input
        sequence if possible (e.g., strings become strings, other iterables become lists).

    Raises:
        ValueError: If size is not a positive integer.
    """
    if not isinstance(size, int) or size <= 0:
        raise ValueError("size must be a positive integer")
    # Convert to list for indexing; keep original for type handling
    items = list(seq)
    chunks = [items[i:i + size] for i in range(0, len(items), size)]
    # Preserve string type when input is a string
    if isinstance(seq, str):
        return [''.join(chunk) for chunk in chunks]
    return chunks


if __name__ == "__main__":
    # Test with list input
    assert chunked([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    # Test with string input
    assert chunked("abcdefg", 3) == ["abc", "def", "g"]
    # Test with tuple input (converted to list chunks)
    assert chunked((0, 1, 2, 3, 4), 2) == [[0, 1], [2, 3], [4]]
    # Test size equal to length
    assert chunked([1, 2, 3], 3) == [[1, 2, 3]]
    # Test size larger than length
    assert chunked([1, 2], 5) == [[1, 2]]
    # Test invalid size
    try:
        chunked([1, 2, 3], 0)
        raise AssertionError("Expected ValueError for size 0")
    except ValueError:
        pass
    try:
        chunked([1, 2, 3], -1)
        raise AssertionError("Expected ValueError for negative size")
    except ValueError:
        pass
    print("All tests passed.")