# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def unique_preserve_order(iterable):
    """
    Return a list of unique elements from the given iterable while preserving the original order.

    Args:
        iterable: An iterable containing hashable items.

    Returns:
        List containing the first occurrence of each unique item in the order they appeared.
    """
    seen = set()
    result = []
    for item in iterable:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


if __name__ == "__main__":
    # Test cases for unique_preserve_order
    test_cases = [
        {
            "input": [1, 2, 3, 2, 1, 4, 5, 3],
            "expected": [1, 2, 3, 4, 5],
        },
        {
            "input": ["a", "b", "a", "c", "b", "d"],
            "expected": ["a", "b", "c", "d"],
        },
        {
            "input": [],
            "expected": [],
        },
        {
            "input": [None, None, 0, False, 0, None],
            "expected": [None, 0, False],
        },
    ]

    for idx, case in enumerate(test_cases, 1):
        output = unique_preserve_order(case["input"])
        if output != case["expected"]:
            raise AssertionError(
                f"Test case {idx} failed: input={case['input']}, expected={case['expected']}, got={output}"
            )
    # If all tests pass, exit normally (process exit code 0).