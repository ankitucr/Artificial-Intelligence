def lcm(a, b):
    def gcd(x, y):
        while y:
            x, y = y, x % y
        return x
    return a * b // gcd(a, b)