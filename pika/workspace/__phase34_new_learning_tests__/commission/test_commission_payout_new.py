from commission_payout_new import payout

def test_payout():
    r = payout(2000, 5, 300)
    assert r["commission"] == 100, r
    assert r["payout"] == 400, r

if __name__ == "__main__":
    test_payout()
    print("COMMISSION TEST PASS")
