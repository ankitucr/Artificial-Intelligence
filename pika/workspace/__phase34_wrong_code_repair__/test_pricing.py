from pricing import discount

def test_discount():
    assert discount(100, 20) == 80
    assert discount(200, 10) == 180
    assert discount(50, 0) == 50

if __name__ == "__main__":
    test_discount()
    print("INDEPENDENT TEST PASS")
