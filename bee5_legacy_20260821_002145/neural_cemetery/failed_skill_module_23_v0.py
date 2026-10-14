# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def flatten(iterable):
    """
    Recursively flatten a nested iterable (list, tuple, set, etc.) into a flat list.
    Strings are treated as atomic and not iterated over.

    Parameters
    ----------
    iterable : any iterable
        The potentially nested iterable to flatten.

    Returns
    -------
    list
        A flat list containing all non-iterable leaf elements.
    """
    result = []
    stack = [iter(iterable)]
    while stack:
        try:
            item = next(stack[-1])
        except StopIteration:
            stack.pop()
            continue

        # Strings (and bytes) are considered atomic
        if isinstance(item, (str, bytes)):
            result.append(item)
        else:
            try:
                # Try to get an iterator; if it works, it's a nested iterable
                sub_iter = iter(item)
            except TypeError:
                result.append(item)
            else:
                # Push the new iterator onto the stack
                stack.append(sub_iter)
    return result


if __name__ == "__main__":
    # Test cases
    test_cases = [
        ([1, 2, 3], [1, 2, 3]),
        ([[1, 2], [3, 4]], [1, 2, 3, 4]),
        ([1, [2, [3, [4]], 5]], [1, 2, 3, 4, 5]),
        ([], []),
        (["a", ["b", ["c"]]], ["a", "b", "c"]),
        (["hello", ["world", ["!"]]], ["hello", "world", "!"]),
        (["abc", ["de", ["f"]]], ["abc", "de", "f"]),
        ((1, (2, (3,)), 4), [1, 2, 3, 4]),
        ({1, 2, (3, 4)}, [1, 2, 3, 4]),
        (["a", ("b", ["c", ("d",)])], ["a", "b", "c", "d"]),
        (["a", b"bytes"], ["a", b"bytes"]),  # bytes are atomic as well
    ]

    for idx, (inp, expected) in enumerate(test_cases, 1):
        result = flatten(inp)
        # Since sets are unordered, sort before comparison when input contains a set
        if isinstance(inp, set):
            result = sorted(result)
            expected = sorted(expected)
        if result != expected:
            raise AssertionError(f"Test case {idx} failed: expected {expected}, got {result}")

    # Additional test: generator input
    def gen():
        yield 1
        yield [2, 3]
        yield (4, (5,))

    if flatten(gen()) != [1, 2, 3, 4, 5]:
        raise AssertionError("Generator test failed")

    # All tests passed
    print("All flatten tests passed.")