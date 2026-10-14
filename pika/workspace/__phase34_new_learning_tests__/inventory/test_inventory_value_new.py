from inventory_value_new import inventory_value

def test_inventory():
    r = inventory_value([
        {"sku": "A", "price": 12, "quantity": 3},
        {"sku": "B", "price": 5, "quantity": 10},
    ], reorder_at=5)
    assert r["total_value"] == 86, r
    assert r["reorder"] == ["A"], r

if __name__ == "__main__":
    test_inventory()
    print("INVENTORY TEST PASS")
