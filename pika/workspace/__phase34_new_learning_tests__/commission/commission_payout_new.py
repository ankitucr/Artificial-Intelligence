def payout(sales, commission_percent, base_pay):
    commission = sales * (commission_percent / 100)
    total = base_pay + commission
    return {"commission": commission, "payout": total}
