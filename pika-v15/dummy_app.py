def calculate_total(prices):
    total = 0
    for price in prices:
        if price is None:
            continue
        total += price
    return total
