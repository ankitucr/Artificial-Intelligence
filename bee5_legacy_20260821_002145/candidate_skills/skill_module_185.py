def roman_numeral_converter(**kwargs):
    roman_numerals = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    int_to_roman = {1: 'I', 4: 'IV', 5: 'V', 9: 'IX', 10: 'X', 40: 'XL', 50: 'L', 90: 'XC', 100: 'C', 400: 'CD', 500: 'D', 900: 'CM', 1000: 'M'}
    if 'num' in kwargs:
        num = kwargs['num']
        result = ''
        for value in sorted(int_to_roman.keys(), reverse=True):
            while num >= value:
                result += int_to_roman[value]
                num -= value
        return result
    elif 'roman' in kwargs:
        roman = kwargs['roman']
        result = 0
        i = 0
        while i < len(roman):
            if i + 1 < len(roman) and roman_numerals[roman[i]] < roman_numerals[roman[i+1]]:
                result += roman_numerals[roman[i+1]] - roman_numerals[roman[i]]
                i += 2
            else:
                result += roman_numerals[roman[i]]
                i += 1
        return result
    else:
        return None