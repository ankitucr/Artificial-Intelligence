def calculate_statistics(data):
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    standard_deviation = variance ** 0.5
    return mean, variance, standard_deviation

def find_mode(data):
    frequency = {}
    for num in data:
        frequency[num] = frequency.get(num, 0) + 1
    max_frequency = max(frequency.values())
    modes = [num for num, freq in frequency.items() if freq == max_frequency]
    return modes

def analyze_data(data):
    mean, variance, standard_deviation = calculate_statistics(data)
    mode = find_mode(data)
    return {
        'mean': mean,
        'variance': variance,
        'standard_deviation': standard_deviation,
        'mode': mode
    }

def main():
    data = [1, 2, 3, 4, 4, 5, 5, 5]
    result = analyze_data(data)
    print("Mean:", result['mean'])
    print("Variance:", result['variance'])
    print("Standard Deviation:", result['standard_deviation'])
    print("Mode:", result['mode'])

if __name__ == "__main__":
    main()