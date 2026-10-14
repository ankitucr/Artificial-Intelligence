def inventory_value(items, reorder_at=5):
    total = 0
    reorder = []
    for item in items:
        total += item.get("price", 0)
        if item.get("quantity", 0) > reorder_at:
            reorder.append(item.get("sku"))
    return {"total_value": total, "reorder": reorder}
