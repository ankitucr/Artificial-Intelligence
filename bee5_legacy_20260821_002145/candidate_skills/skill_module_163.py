def lcm(*args):
    def gcd(a, b):
        while b:
            a, b = b, a % b
        return a
    result = args[0]
    for num in args[1:]:
        result = result * num // gcd(result, num)
    return result