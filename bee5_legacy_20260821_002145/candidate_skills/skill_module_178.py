def lcm(*numbers):
    def gcd(a, b):
        while b:
            a, b = b, a % b
        return a
    result = numbers[0]
    for num in numbers[1:]:
        result = result * num // gcd(result, num)
    return result