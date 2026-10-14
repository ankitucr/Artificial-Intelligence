def calculate_statistics(data):
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    standard_deviation = variance ** 0.5
    median = sorted(data)[len(data) // 2]
    mode = max(set(data), key=data.count)
    return mean, variance, standard_deviation, median, mode

def analyze_data(data):
    mean, variance, standard_deviation, median, mode = calculate_statistics(data)
    print(f"Mean: {mean}")
    print(f"Variance: {variance}")
    print(f"Standard Deviation: {standard_deviation}")
    print(f"Median: {median}")
    print(f"Mode: {mode}")

def main():
    data = [1, 2, 3, 4, 5]
    analyze_data(data)

if __name__ == "__main__":
    main()