import numpy as np
import matplotlib.pyplot as plt

# ---- Network Parameters ----
num_neurons = 5
threshold = 1.0
reset_potential = 0.0
leak_rate = 0.05
time_steps = 200

# ---- Connection weights (synapses) ----
# weight[i][j] = neuron i se neuron j ko kitna signal jata hai jab i fire kare
weights = np.zeros((num_neurons, num_neurons))
weights[0][1] = 1.2   # Neuron 0 -> 1
weights[1][2] = 1.2   # Neuron 1 -> 2
weights[2][3] = 1.2   # Neuron 2 -> 3
weights[3][4] = 1.2   # Neuron 3 -> 4o

# ---- State variables ----
membrane_potential = np.zeros(num_neurons)
potential_history = [[] for _ in range(num_neurons)]
spike_times = [[] for _ in range(num_neurons)]

# ---- External input sirf Neuron 0 ko milega ----
external_input = np.zeros(num_neurons)
external_input[0] = 0.08

# ---- Simulation Loop ----
for t in range(time_steps):
    incoming_signal = np.zeros(num_neurons)

    # Leak
    membrane_potential -= leak_rate * membrane_potential

    # External input add karo
    membrane_potential += external_input

    # Check kaun fire kar raha hai
    fired = membrane_potential >= threshold

    for i in range(num_neurons):
        if fired[i]:
            spike_times[i].append(t)
            membrane_potential[i] = reset_potential
            # Is neuron ka spike, connected neurons ko signal bhejega (agle step mein)
            for j in range(num_neurons):
                if weights[i][j] > 0:
                    incoming_signal[j] += weights[i][j]

    # Connected neurons ka signal add karo (agle step ke effect ke liye)
    membrane_potential += incoming_signal

    for i in range(num_neurons):
        potential_history[i].append(membrane_potential[i])

# ---- Results print karo ----
for i in range(num_neurons):
    print(f"Neuron {i}: {len(spike_times[i])} spikes at {spike_times[i]}")

# ---- Graph banao ----
fig, axes = plt.subplots(num_neurons, 1, figsize=(10, 10), sharex=True)
for i in range(num_neurons):
    axes[i].plot(potential_history[i])
    axes[i].axhline(y=threshold, color='r', linestyle='--', alpha=0.5)
    for spike in spike_times[i]:
        axes[i].axvline(x=spike, color='g', alpha=0.3)
    axes[i].set_ylabel(f"N{i}")

axes[-1].set_xlabel("Time step")
plt.suptitle("Chain Network: Neuron 0 -> 1 -> 2 -> 3 -> 4")
plt.tight_layout()
plt.savefig("network_output.png")
print("Graph saved as network_output.png")
