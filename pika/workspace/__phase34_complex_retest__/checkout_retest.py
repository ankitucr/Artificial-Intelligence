def checkout(items, discount_percent=0, tax_rate=0.08, shipping=10):
    subtotal = 0
    for item in items:
        subtotal += item.get("price", 0) * item.get("quantity", 1)

    discount = subtotal * discount_percent / 100
    taxable = subtotal - discount
    tax = taxable * tax_rate

    if subtotal >= 100:
        shipping = 0
    else:
        shipping = shipping

    total = subtotal - discount + tax + shipping

    return {
        "subtotal": subtotal,
        "discount": discount,
        "tax": tax,
        "shipping": shipping,
        "total": total,
    }