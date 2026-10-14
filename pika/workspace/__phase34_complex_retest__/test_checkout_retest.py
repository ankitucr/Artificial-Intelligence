from checkout_retest import checkout

def close(a, b):
    assert abs(a - b) < 0.0001, f"expected {b}, got {a}"

def test_quantities_and_totals():
    r = checkout([
        {"price": 20, "quantity": 2},
        {"price": 10, "quantity": 3},
    ], discount_percent=10, tax_rate=0.10, shipping=5)
    close(r["subtotal"], 70)
    close(r["discount"], 7)
    close(r["tax"], 6.3)
    close(r["shipping"], 5)
    close(r["total"], 74.3)

def test_free_shipping():
    r = checkout(
        [{"price": 60, "quantity": 2}],
        discount_percent=0, tax_rate=0, shipping=8
    )
    close(r["subtotal"], 120)
    close(r["shipping"], 0)
    close(r["total"], 120)

def test_empty_and_regular_cart():
    r = checkout(
        [{"price": 25, "quantity": 2}],
        discount_percent=0, tax_rate=0.08, shipping=5
    )
    close(r["subtotal"], 50)
    close(r["discount"], 0)
    close(r["tax"], 4)
    close(r["shipping"], 5)
    close(r["total"], 59)

    e = checkout([], discount_percent=0, tax_rate=0, shipping=5)
    close(e["subtotal"], 0)
    close(e["discount"], 0)
    close(e["tax"], 0)
    close(e["shipping"], 5)
    close(e["total"], 5)

if __name__ == "__main__":
    test_quantities_and_totals()
    test_free_shipping()
    test_empty_and_regular_cart()
    print("COMPLEX RETEST PASS")
