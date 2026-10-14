import numpy as np
import matplotlib.pyplot as plt
import os

# ---- Network Size ----
num_patterns = 10
num_neurons = num_patterns * 3

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

noise_level = 0.03   # Kitna random disturbance har step pe add hoga

# ---- Weight matrix ----
weights = np.zeros((num_neurons, num_neurons))
for i in range(num_patterns):
    for h in range(num_patterns):
        weights[input_idx[i]][hidden_idx[h]] = 1.15 if i == h else 0.5
for h in range(num_patterns):
    for o in range(num_patterns):
        weights[hidden_idx[h]][output_idx[o]] = 1.15 if h == o else 0.5

connection_mask = weights > 0

# ---- State ----
membrane_potential = np.zeros(num_neurons)
spike_counts = np.zeros(num_neurons, dtype=int)
correct_output_count = 0
total_trials = 0
last_fired = np.full(num_neurons, -100)
last_pattern = -1

track_correct = [(input_idx[k], hidden_idx[k]) for k in range(num_patterns)]
track_wrong = [(input_idx[0], hidden_idx[1])]
weight_history_correct = {p: [] for p in track_correct}
weight_history_wrong = {p: [] for p in track_wrong}

# ---- Simulation Loop ----
for t in range(time_steps):
    pattern = (t // block_size) % num_patterns

    if pattern != last_pattern:
        last_pattern = pattern
        total_trials += 1

    external_input = np.zeros(num_neurons)
    external_input[input_idx[pattern]] = 0.08

    # ---- NOISE add karo (real brain jaisa random disturbance) ----
    noise = np.random.uniform(-noise_level, noise_level, num_neurons)
    membrane_potential += noise

    membrane_potential -= leak_rate * membrane_potential
    membrane_potential += external_input

    fired = membrane_potential >= threshold
    fired_idx = np.where(fired)[0]

    if len(fired_idx) > 0:
        spike_counts[fired_idx] += 1
        membrane_potential[fired_idx] = reset_potential
        last_fired[fired_idx] = t

        # Check karo sahi output fire hua ya nahi
        for idx in fired_idx:
            if idx in output_idx:
                correct_output = output_idx[pattern]
                if idx == correct_output:
                    correct_output_count += 1

        incoming_signal = weights[fired_idx, :].sum(axis=0)
        membrane_potential += incoming_signal

    if len(fired_idx) > 0:
        for j in fired_idx:
            connected_i = np.where(connection_mask[:, j])[0]
            recently_fired = (0 <= (t - last_fired[connected_i])) & ((t - last_fired[connected_i]) <= 5) & (last_fired[connected_i] != -100)
            weights[connected_i[recently_fired], j] = np.minimum(max_weight, weights[connected_i[recently_fired], j] + learning_rate)
            weights[connected_i[~recently_fired], j] = np.maximum(min_weight, weights[connected_i[~recently_fired], j] - decay_rate)

    for p in track_correct:
        weight_history_correct[p].append(weights[p[0]][p[1]])
    for p in track_wrong:
        weight_history_wrong[p].append(weights[p[0]][p[1]])

# ---- Results ----
print(f"Total neurons: {num_neurons}, Noise level: {noise_level}")
print(f"\nCorrect output fires: {correct_output_count}")
print(f"Total output spikes: {spike_counts[output_idx].sum()}")
accuracy = (correct_output_count / spike_counts[output_idx].sum()) * 100 if spike_counts[output_idx].sum() > 0 else 0
print(f"Accuracy: {accuracy:.1f}%")

print("\nSample final weights:")
for k in range(min(5, num_patterns)):
    correct_w = weights[input_idx[k]][hidden_idx[k]]
    wrong_w = weights[input_idx[k]][hidden_idx[(k+1) % num_patterns]]
    print(f"  Pattern {k}: correct={correct_w:.3f}, wrong={wrong_w:.3f}")

# ---- Graph ----
plt.figure(figsize=(10, 5))
for p, hist in weight_history_correct.items():
    plt.plot(hist, color='green', alpha=0.5)
for p, hist in weight_history_wrong.items():
    plt.plot(hist, color='red', alpha=0.7, label="Sample wrong connection")
plt.plot([], [], color='green', label="Correct connections (all patterns)")
plt.xlabel("Time step")
plt.ylabel("Weight")
plt.title(f"Noisy Network (noise={noise_level}): {accuracy:.1f}% accuracy")
plt.legend()

save_path = os.path.expanduser("~/storage/pictures/brain_project/noisy_network_output.png")
plt.savefig(save_path)
print(f"\nGraph saved to Gallery: {save_path}")
