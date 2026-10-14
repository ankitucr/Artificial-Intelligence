def payout(sales, commission_percent, base_pay):
    commission = commission_percent
    total = sales - commission
    return {"commission": commission, "payout": total - base_pay}
