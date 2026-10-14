from checkout import checkout

def close(a, b):
    assert abs(a - b) < 0.0001, f"expected {b}, got {a}"

def test_quantities_and_totals():
    result = checkout([
        {"price": 20, "quantity": 2},
        {"price": 10, "quantity": 3},
    ], discount_percent=10, tax_rate=0.10, shipping=5)

    close(result["subtotal"], 70)
    close(result["discount"], 7)
    close(result["tax"], 6.3)
    close(result["shipping"], 5)
    close(result["total"], 74.3)

def test_free_shipping_threshold():
    result = checkout(
        [{"price": 60, "quantity": 2}],
        discount_percent=0,
        tax_rate=0,
        shipping=8,
    )
    close(result["subtotal"], 120)
    close(result["shipping"], 0)
    close(result["total"], 120)

def test_no_discount_and_empty_cart():
    result = checkout(
        [{"price": 25, "quantity": 2}],
        discount_percent=0,
        tax_rate=0.08,
        shipping=5,
    )
    close(result["subtotal"], 50)
    close(result["discount"], 0)
    close(result["tax"], 4)
    close(result["shipping"], 5)
    close(result["total"], 59)

    empty = checkout([], discount_percent=0, tax_rate=0, shipping=5)
    close(empty["subtotal"], 0)
    close(empty["discount"], 0)
    close(empty["tax"], 0)
    close(empty["shipping"], 5)
    close(empty["total"], 5)

if __name__ == "__main__":
    test_quantities_and_totals()
    test_free_shipping_threshold()
    test_no_discount_and_empty_cart()
    print("ALL CHECKOUT TESTS PASS")
