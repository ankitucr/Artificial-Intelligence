import numpy as np
import matplotlib.pyplot as plt

# ---- Network Parameters ----
num_neurons = 5
threshold = 1.0
reset_potential = 0.0
leak_rate = 0.05
time_steps = 300

# ---- Hebbian learning parameters ----
learning_rate = 0.02   # Kitni tezi se weight badhega
max_weight = 2.0       # Weight itna zyada nahi ho sakta (real synapse ki tarah limit hoti hai)
weight_decay = 0.001    # Agar saath fire na hon, weight thoda kam bhi hota hai

# ---- Starting weights (chhote se shuru, "seekhna" abhi baaki hai) ----
weights = np.zeros((num_neurons, num_neurons))
weights[0][1] = 1.1   # Kaam karne layak, lekin abhi weak-ish
weights[1][2] = 1.1
weights[2][3] = 1.1
weights[3][4] = 1.1
# ---- State variables ----
membrane_potential = np.zeros(num_neurons)
potential_history = [[] for _ in range(num_neurons)]
spike_times = [[] for _ in range(num_neurons)]
weight_history = {(0,1): [], (1,2): [], (2,3): [], (3,4): []}

# ---- External input sirf Neuron 0 ko milega ----
external_input = np.zeros(num_neurons)
external_input[0] = 0.08

# ---- Track karo kaun kab last fire hua tha (Hebbian rule ke liye) ----
last_fired = np.full(num_neurons, -100)

# ---- Simulation Loop ----
for t in range(time_steps):
    incoming_signal = np.zeros(num_neurons)

    # Leak
    membrane_potential -= leak_rate * membrane_potential

    # External input
    membrane_potential += external_input

    # Check kaun fire kar raha hai
    fired = membrane_potential >= threshold

    for i in range(num_neurons):
        if fired[i]:
            spike_times[i].append(t)
            membrane_potential[i] = reset_potential
            last_fired[i] = t

            # Signal agle connected neuron ko bhejo
            for j in range(num_neurons):
                if weights[i][j] > 0:
                    incoming_signal[j] += weights[i][j]

    membrane_potential += incoming_signal

    # ---- HEBBIAN LEARNING RULE ----
    # Agar neuron i ne fire kiya, aur neuron j turant baad (5 steps ke andar) fire kare -> weight badhao
    for i in range(num_neurons):
        for j in range(num_neurons):
            if weights[i][j] > 0:  # Sirf existing connections update karo
                if fired[i] and 0 < (t - last_fired[j]) <= 5 and last_fired[j] != -100:
                    pass  # (ye case rare hai yahan, simple chain mein)
                # Simple version: agar i abhi fire hua aur j jaldi hi fire hoga (agle steps mein), weight badhao
                if fired[i] and fired[j] == False:
                    pass

    # Yahan hum simpler tareeka use karenge: agar i aur j dono is time-window mein fire hue -> strengthen
    for (i, j) in [(0,1), (1,2), (2,3), (3,4)]:
        if abs(last_fired[i] - last_fired[j]) <= 3 and last_fired[i] != -100 and last_fired[j] != -100:
            if last_fired[j] > last_fired[i]:  # j, i ke baad fire hua (sahi order)
                weights[i][j] = min(max_weight, weights[i][j] + learning_rate)
        else:
            weights[i][j] = max(0.1, weights[i][j] - weight_decay)  # thoda decay

    for i in range(num_neurons):
        potential_history[i].append(membrane_potential[i])
    for pair in weight_history:
        weight_history[pair].append(weights[pair[0]][pair[1]])

# ---- Results print karo ----
for i in range(num_neurons):
    print(f"Neuron {i}: {len(spike_times[i])} spikes")

print("\nFinal weights:")
for pair in weight_history:
    print(f"  {pair}: {weights[pair[0]][pair[1]]:.3f}")

# ---- Graph: Weight growth over time ----
plt.figure(figsize=(10, 5))
for pair, history in weight_history.items():
    plt.plot(history, label=f"Weight {pair}")
plt.xlabel("Time step")
plt.ylabel("Synaptic Weight")
plt.title("Hebbian Learning: Weights Growing Over Time")
plt.legend()
plt.savefig("hebbian_output.png")
print("\nGraph saved as hebbian_output.png")

