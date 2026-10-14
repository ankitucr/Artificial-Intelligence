import numpy as np
import matplotlib.pyplot as plt

# ---- Network Size ----
num_patterns = 10          # Kitne alag patterns discriminate karne hain
num_neurons = num_patterns * 3   # Input + Hidden + Output

input_idx = list(range(0, num_patterns))
hidden_idx = list(range(num_patterns, num_patterns*2))
output_idx = list(range(num_patterns*2, num_patterns*3))

threshold = 1.0
reset_potential = 0.0
leak_rate = 0.05
time_steps = 6000
block_size = 40

learning_rate = 0.05
decay_rate = 0.03
max_weight = 2.0
min_weight = 0.1

# ---- Weight matrix (vectorized) ----
weights = np.zeros((num_neurons, num_neurons))
for i in range(num_patterns):
    for h in range(num_patterns):
        weights[input_idx[i]][hidden_idx[h]] = 1.15 if i == h else 0.5
for h in range(num_patterns):
    for o in range(num_patterns):
        weights[hidden_idx[h]][output_idx[o]] = 1.15 if h == o else 0.5

connection_mask = weights > 0  # Kaunse connections exist karte hain

# ---- State ----
membrane_potential = np.zeros(num_neurons)
spike_counts = np.zeros(num_neurons, dtype=int)
last_fired = np.full(num_neurons, -100)

# Sirf diagonal (sahi) aur ek sample cross connection track karenge graph ke liye
track_correct = [(input_idx[k], hidden_idx[k]) for k in range(num_patterns)]
track_wrong = [(input_idx[0], hidden_idx[1])]  # sample galat connection
weight_history_correct = {p: [] for p in track_correct}
weight_history_wrong = {p: [] for p in track_wrong}

# ---- Simulation Loop (vectorized) ----
for t in range(time_steps):
    pattern = (t // block_size) % num_patterns
    external_input = np.zeros(num_neurons)
    external_input[input_idx[pattern]] = 0.08

    # Leak + input
    membrane_potential -= leak_rate * membrane_potential
    membrane_potential += external_input

    # Kaun fire hua
    fired = membrane_potential >= threshold
    fired_idx = np.where(fired)[0]

    if len(fired_idx) > 0:
        spike_counts[fired_idx] += 1
        membrane_potential[fired_idx] = reset_potential
        last_fired[fired_idx] = t

        # Signal propagate karo (matrix row sum for fired neurons)
        incoming_signal = weights[fired_idx, :].sum(axis=0)
        membrane_potential += incoming_signal

    # ---- Hebbian Learning (vectorized, sirf fired[j] wale update honge) ----
    if len(fired_idx) > 0:
        for j in fired_idx:
            # Konse i neurons is j se connected hain
            connected_i = np.where(connection_mask[:, j])[0]
            recently_fired = (0 <= (t - last_fired[connected_i])) & ((t - last_fired[connected_i]) <= 5) & (last_fired[connected_i] != -100)
            weights[connected_i[recently_fired], j] = np.minimum(max_weight, weights[connected_i[recently_fired], j] + learning_rate)
            weights[connected_i[~recently_fired], j] = np.maximum(min_weight, weights[connected_i[~recently_fired], j] - decay_rate)

    for p in track_correct:
        weight_history_correct[p].append(weights[p[0]][p[1]])
    for p in track_wrong:
        weight_history_wrong[p].append(weights[p[0]][p[1]])

# ---- Results ----
print(f"Total neurons: {num_neurons} ({num_patterns} patterns x 3 layers)")
print(f"\nInput spikes: {spike_counts[input_idx]}")
print(f"Hidden spikes: {spike_counts[hidden_idx]}")
print(f"Output spikes: {spike_counts[output_idx]}")

print("\n---- Sample Input->Hidden weights (diagonal = correct) ----")
for k in range(min(5, num_patterns)):
    correct_w = weights[input_idx[k]][hidden_idx[k]]
    wrong_w = weights[input_idx[k]][hidden_idx[(k+1) % num_patterns]]
    print(f"  Pattern {k}: correct={correct_w:.3f}, wrong(sample)={wrong_w:.3f}")

# ---- Graph ----
plt.figure(figsize=(10, 5))
for p, hist in weight_history_correct.items():
    plt.plot(hist, color='green', alpha=0.5)
for p, hist in weight_history_wrong.items():
    plt.plot(hist, color='red', alpha=0.7, label="Sample wrong connection")
plt.plot([], [], color='green', label="Correct connections (all patterns)")
plt.xlabel("Time step")
plt.ylabel("Weight")
plt.title(f"Big Network: {num_patterns} Patterns, {num_neurons} Neurons")
plt.legend()
plt.savefig("big_network_output.png")
print("\nGraph saved as big_network_output.png")
