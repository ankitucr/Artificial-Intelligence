import numpy as np
import matplotlib.pyplot as plt

# ---- LIF Neuron Parameters ----
threshold = 1.0        # Is potential ke paar spike fire hogi
reset_potential = 0.0  # Spike ke baad potential yahan reset hoga
leak_rate = 0.05        # Har step potential thoda kam hoga (leak)
input_current = 0.08    # Har step neuron ko milne wala input
time_steps = 200        # Kitne steps tak simulate karna hai

# ---- State variables ----
membrane_potential = 0.0
potential_history = []
spike_times = []

# ---- Simulation Loop ----
for t in range(time_steps):
    # Leak: potential naturally thoda kam hota hai
    membrane_potential -= leak_rate * membrane_potential

    # Input current add karo
    membrane_potential += input_current

    # Check karo threshold cross hua ya nahi
    if membrane_potential >= threshold:
        spike_times.append(t)
        membrane_potential = reset_potential  # Fire ho gaya, reset karo

    potential_history.append(membrane_potential)

# ---- Results print karo ----
print(f"Total spikes fired: {len(spike_times)}")
print(f"Spike times: {spike_times}")

# ---- Graph banao aur save karo ----
plt.figure(figsize=(10, 4))
plt.plot(potential_history, label="Membrane Potential")
plt.axhline(y=threshold, color='r', linestyle='--', label="Threshold")

for spike in spike_times:
    plt.axvline(x=spike, color='g', alpha=0.3)

plt.xlabel("Time step")
plt.ylabel("Membrane Potential")
plt.title("LIF Neuron Simulation")
plt.legend()
plt.savefig("lif_neuron_output.png")
print("Graph saved as lif_neuron_output.png")
