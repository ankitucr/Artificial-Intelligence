import numpy as np
import matplotlib.pyplot as plt
import os

# ---- Network Setup ----
num_patterns = 10
num_neurons = num_patterns * 3
input_idx = list(range(0, num_patterns))
hidden_idx = list(range(num_patterns, num_patterns*2))
output_idx = list(range(num_patterns*2, num_patterns*3))

threshold = 1.0
reset_potential = 0.0
leak_rate = 0.05
block_size = 40

learning_rate = 0.05
decay_rate = 0.03
max_weight = 2.0
min_weight = 0.1
noise_level = 0.083
inhibition_strength = 2.0   # Jitna zyada, utna strong "winner takes all"
external_input_strength = 0.20   # 0.08 se badhaya, zyada firing frequency ke liye

train_steps = 20000
test_steps = 2000

weights = np.zeros((num_neurons, num_neurons))
for i in range(num_patterns):
    for h in range(num_patterns):
        weights[input_idx[i]][hidden_idx[h]] = 1.15 if i == h else 0.5
for h in range(num_patterns):
    for o in range(num_patterns):
        weights[hidden_idx[h]][output_idx[o]] = 1.15 if h == o else 0.5

connection_mask = weights > 0

membrane_potential = np.zeros(num_neurons)
last_fired = np.full(num_neurons, -100)


def apply_lateral_inhibition(fired_idx, layer_idx, membrane_potential):
    """Jab ek neuron fire ho, usi layer ke doosre neurons ko thoda suppress karo"""
    layer_fired = [i for i in fired_idx if i in layer_idx]
    if len(layer_fired) > 0:
        for other in layer_idx:
            if other not in layer_fired:
                membrane_potential[other] -= inhibition_strength
    return membrane_potential


def run_step(t, pattern, learning_on):
    global membrane_potential, last_fired, weights

    # ---- FIX: block-boundary reset (crosstalk khatam karne ke liye) ----
    if t % block_size == 0:
        membrane_potential[:] = 0.0

    external_input = np.zeros(num_neurons)
    external_input[input_idx[pattern]] = external_input_strength

    noise = np.random.uniform(-noise_level, noise_level, num_neurons)
    membrane_potential += noise
    membrane_potential -= leak_rate * membrane_potential
    membrane_potential += external_input

    fired = membrane_potential >= threshold
    fired_idx = np.where(fired)[0]

    correct_fire = False
    output_fired = False

    if len(fired_idx) > 0:
        membrane_potential[fired_idx] = reset_potential
        last_fired[fired_idx] = t

        # ---- Lateral inhibition: hidden aur output layers mein "winner takes all" ----
        membrane_potential[:] = apply_lateral_inhibition(fired_idx, hidden_idx, membrane_potential)
        membrane_potential[:] = apply_lateral_inhibition(fired_idx, output_idx, membrane_potential)

        for idx in fired_idx:
            if idx in output_idx:
                output_fired = True
                if idx == output_idx[pattern]:
                    correct_fire = True

        incoming_signal = weights[fired_idx, :].sum(axis=0)
        membrane_potential += incoming_signal

        if learning_on:
            for j in fired_idx:
                connected_i = np.where(connection_mask[:, j])[0]
                recently = (0 <= (t - last_fired[connected_i])) & ((t - last_fired[connected_i]) <= 5) & (last_fired[connected_i] != -100)
                weights[connected_i[recently], j] = np.minimum(max_weight, weights[connected_i[recently], j] + learning_rate)
                weights[connected_i[~recently], j] = np.maximum(min_weight, weights[connected_i[~recently], j] - decay_rate)

    return output_fired, correct_fire


# ---- TRAINING PHASE ----
print(f"Training for {train_steps} steps...")
for t in range(train_steps):
    pattern = (t // block_size) % num_patterns
    run_step(t, pattern, learning_on=True)

print("Training done. Weights locked. Starting test phase...\n")

# ---- TESTING PHASE (learning off) ----
correct = 0
total_output = 0
for t in range(train_steps, train_steps + test_steps):
    pattern = (t // block_size) % num_patterns
    output_fired, correct_fire = run_step(t, pattern, learning_on=False)
    if output_fired:
        total_output += 1
        if correct_fire:
            correct += 1

accuracy = (correct / total_output * 100) if total_output > 0 else 0

print(f"---- TEST RESULTS (after training, with inhibition + block reset) ----")
print(f"Noise level: {noise_level}, Inhibition strength: {inhibition_strength}")
print(f"Correct: {correct} / {total_output}")
print(f"Test Accuracy: {accuracy:.1f}%")

print("\nSample final weights:")
for k in range(min(5, num_patterns)):
    cw = weights[input_idx[k]][hidden_idx[k]]
    ww = weights[input_idx[k]][hidden_idx[(k+1) % num_patterns]]
    print(f"  Pattern {k}: correct={cw:.3f}, wrong={ww:.3f}")

# ---- Simple bar graph: accuracy ----
plt.figure(figsize=(6, 5))
plt.bar(["Test Accuracy"], [accuracy], color='green')
plt.ylim(0, 100)
plt.ylabel("Accuracy (%)")
plt.title(f"Trained Network with Lateral Inhibition + Block Reset\n({accuracy:.1f}% accuracy on unseen test steps)")
plt.text(0, accuracy + 2, f"{accuracy:.1f}%", ha='center', fontsize=14)

save_path = os.path.expanduser("~/storage/pictures/brain_project/brain_v2_output.png")
plt.savefig(save_path)
print(f"\nGraph saved: {save_path}")
