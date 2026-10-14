def checkout(items, discount_percent=0, tax_rate=0.08, shipping=10):
    subtotal = 0
    for item in items:
        subtotal += item.get("price", 0)

    discount = discount_percent
    taxable = subtotal + discount
    tax = taxable * tax_rate

    if subtotal > 100:
        shipping = 10
    else:
        shipping = 0

    total = subtotal + discount + tax - shipping

    return {
        "subtotal": total,
        "discount": discount,
        "tax": tax,
        "shipping": shipping,
        "total": subtotal,
    }
