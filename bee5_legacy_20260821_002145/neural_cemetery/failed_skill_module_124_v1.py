# ==================================================
# FAILED EXPERIMENT
# ==================================================
# Skill: skill_module_124
# Version: 1
# Time: 2026-08-20 16:23:39
#
# FAILURE REPORT
# --------------------------------------------------
# SYNTAX ERROR
# Line: 30
# Column: 15
# Message: '[' was never closed
# Code: numbers = [1, 2, 3,
# ==================================================

def calculate_median(numbers):
    numbers.sort()
    length = len(numbers)
    if length % 2 == 0:
        median = (numbers[length // 2 - 1] + numbers[length // 2]) / 2
    else:
        median = numbers[length // 2]
    return median

def calculate_mode(numbers):
    frequency = {}
    for number in numbers:
        if number in frequency:
            frequency[number] += 1
        else:
            frequency[number] = 1
    max_frequency = max(frequency.values())
    modes = [number for number, freq in frequency.items() if freq == max_frequency]
    return modes

def calculate_statistics(numbers):
    mean = sum(numbers) / len(numbers)
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    standard_deviation = variance ** 0.5
    median = calculate_median(numbers)
    mode = calculate_mode(numbers)
    return mean, variance, standard_deviation, median, mode

def main():
    numbers = [1, 2, 3,