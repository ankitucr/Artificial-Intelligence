# ERROR:
# bionic/linker/linker_cfi.cpp:158: MapShadow CHECK 'p != MAP_FAILED' failed

def is_power_of_two(n):
    """Check if a number is a power of two."""
    if n <= 0:
        return False
    return (n & (n - 1)) == 0

def next_power_of_two(n):
    """Find the next power of two greater than or equal to n."""
    if n <= 0:
        return 1
    n -= 1
    n |= n >> 1
    n |= n >> 2
    n |= n >> 4
    n |= n >> 8
    n |= n >> 16
    return n + 1

def test_is_power_of_two():
    assert is_power_of_two(1)
    assert is_power_of_two(2)
    assert is_power_of_two(4)
    assert is_power_of_two(8)
    assert not is_power_of_two(3)
    assert not is_power_of_two(5)
    assert not is_power_of_two(6)

def test_next_power_of_two():
    assert next_power_of_two(1) == 1
    assert next_power_of_two(2) == 2
    assert next_power_of_two(3) == 4
    assert next_power_of_two(4) == 4
    assert next_power_of_two(5) == 8
    assert next_power_of_two(8) == 8

if __name__ == "__main__":
    test_is_power_of_two()
    test_next_power_of_two()
    if not is_power_of_two(next_power_of_two(10)):
        raise Exception("next_power_of_two failed")
    if next_power_of_two(10) < 10:
        raise Exception("next_power_of_two failed")