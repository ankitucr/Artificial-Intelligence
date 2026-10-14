# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

from typing import Iterable, List, TypeVar, Generator

T = TypeVar('T')


def chunks(seq: Iterable[T], size: int) -> Generator[List[T], None, None]:
    """Yield successive chunks of length `size` from `seq`.

    Args:
        seq: An iterable of items.
        size: Positive integer specifying the maximum size of each chunk.

    Yields:
        Lists containing up to `size` items from `seq` in order.

    Raises:
        ValueError: If `size` is not a positive integer.
    """
    if size <= 0:
        raise ValueError("size must be a positive integer")
    chunk: List[T] = []
    for item in seq:
        chunk.append(item)
        if len(chunk) == size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def chunk_list(lst: List[T], size: int) -> List[List[T]]:
    """Return a list of chunks derived from `lst` using the given `size`."""
    return list(chunks(lst, size))


if __name__ == "__main__":
    # Basic functionality tests
    assert list(chunks([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]
    assert list(chunks([], 3)) == []
    assert chunk_list([1, 2, 3, 4, 5], 3) == [[1, 2, 3], [4, 5]]

    # Size larger than sequence
    assert list(chunks([1, 2], 5)) == [[1, 2]]

    # Non‑positive size should raise
    try:
        list(chunks([1, 2, 3], 0))
        raise AssertionError("Expected ValueError for size 0")
    except ValueError:
        pass

    try:
        list(chunks([1, 2, 3], -1))
        raise AssertionError("Expected ValueError for negative size")
    except ValueError:
        pass

    print("All tests passed.")