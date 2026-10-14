def convert_roman_numeral(value):
    roman_numerals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    if isinstance(value, str):
        result = 0
        for i in range(len(value)):
            if i > 0 and roman_numerals[value[i]] > roman_numerals[value[i - 1]]:
                result += roman_numerals[value[i]] - 2 * roman_numerals[value[i - 1]]
            else:
                result += roman_numerals[value[i]]
        return result
    elif isinstance(value, int):
        result = ''
        while value > 0:
            if value >= 1000:
                result += 'M'
                value -= 1000
            elif value >= 900:
                result += 'CM'
                value -= 900
            elif value >= 500:
                result += 'D'
                value -= 500
            elif value >= 400:
                result += 'CD'
                value -= 400
            elif value >= 100:
                result += 'C'
                value -= 100
            elif value >= 90:
                result += 'XC'
                value -= 90
            elif value >= 50:
                result += 'L'
                value -= 50
            elif value >= 40:
                result += 'XL'
                value -= 40
            elif value >= 10:
                result += 'X'
                value -= 10
            elif value >= 9:
                result += 'IX'
                value -= 9
            elif value >= 5:
                result += 'V'
                value -= 5
            elif value >= 4:
                result += 'IV'
                value -= 4
            elif value >= 1:
                result += 'I'
                value -= 1
        return result
    else:
        raise ValueError('Invalid input type')