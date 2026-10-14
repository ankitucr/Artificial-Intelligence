# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def flatten(iterable):
    """
    Recursively flatten an iterable of arbitrarily nested iterables
    (lists, tuples, sets, etc.) into a flat list.

    Strings and bytes are treated as atomic values and are not iterated
    character‑wise.

    Parameters
    ----------
    iterable : Any
        The object to flatten.

    Returns
    -------
    list
        A flat list containing all non‑iterable leaf elements in depth‑first order.
    """
    result = []

    def _flatten(item):
        # Strings and bytes are considered atomic
        if isinstance(item, (str, bytes)):
            result.append(item)
            return
        # Check for iterable but exclude dictionaries (flatten their keys)
        try:
            iterator = iter(item)
        except TypeError:
            # Not iterable
            result.append(item)
        else:
            # Dictionaries are iterated over their keys
            if isinstance(item, dict):
                for key in item:
                    _flatten(key)
            else:
                for sub in iterator:
                    _flatten(sub)

    _flatten(iterable)
    return result


if __name__ == "__main__":
    # Basic nested list/tuple
    assert flatten([1, [2, [3, 4], 5], 6]) == [1, 2, 3, 4, 5, 6]

    # Mixed types including set and tuple
    mixed = {1, (2, [3, {4, 5}]), 6}
    # Since sets are unordered, sort the result for comparison
    flat_mixed = sorted(flatten(mixed))
    assert flat_mixed == [1, 2, 3, 4, 5, 6]

    # Strings and bytes should be atomic
    assert flatten("abc") == ["abc"]
    assert flatten(b"xyz") == [b"xyz"]

    # Dictionaries: only keys are flattened (values are ignored)
    d = {"a": 1, "b": {"c": 2}}
    assert flatten(d) == ["a", "b", "c"]

    # Empty iterable
    assert flatten([]) == []

    # Non‑iterable input
    assert flatten(42) == [42]

    # Complex nesting with None
    complex_obj = [None, (None, [None])]
    assert flatten(complex_obj) == [None, None, None]

    print("All tests passed.")