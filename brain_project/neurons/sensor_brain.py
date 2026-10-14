#!/usr/bin/env python3

import json
import math
import os
import random
import signal
import subprocess
import time
from collections import deque
from datetime import datetime

# ============================================================
# ANDROID LIVE SENSOR EVOLVING BRAIN
# ============================================================

STATE_FILE = "neurons/sensor_brain_state.json"

MAX_NEURONS = 100
INITIAL_NEURONS = 3

SAMPLE_DELAY = 0.35
NOVELTY_THRESHOLD = 0.28
LEARNING_RATE = 0.12

MIN_FITNESS = 0.08
PRUNE_AFTER_AGE = 250

MEMORY_LIMIT = 1000
TRANSITION_LIMIT = 500

RUNNING = True


# ============================================================
# UTILS
# ============================================================

def now():
    return datetime.now().isoformat(timespec="seconds")


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def distance(a, b):
    if not a or not b:
        return 999.0

    n = min(len(a), len(b))

    if n == 0:
        return 999.0

    s = 0.0

    for i in range(n):
        d = float(a[i]) - float(b[i])
        s += d * d

    return math.sqrt(s / n)


def normalize_value(value, scale):
    try:
        value = float(value)
    except Exception:
        return 0.0

    if not math.isfinite(value):
        return 0.0

    # Stable sigmoid-like normalization
    x = value / max(scale, 1e-9)

    if x > 8:
        return 1.0

    if x < -8:
        return 0.0

    return 0.5 + 0.5 * math.tanh(x)


# ============================================================
# SENSOR BRAIN
# ============================================================

class SensorBrain:

    def __init__(self):

        self.neurons = []
        self.next_id = 0

        self.generation = 0
        self.created_total = 0
        self.pruned_total = 0

        self.states_learned = 0
        self.memory_entries = 0

        self.previous_state = None
        self.previous_winner = None

        self.memory = deque(maxlen=MEMORY_LIMIT)
        self.transitions = deque(maxlen=TRANSITION_LIMIT)

        self.running = True

        self.sensor_names = []

        self.discover_sensors()

        self.load()

        if not self.neurons:
            self.create_initial_neurons()

    # --------------------------------------------------------
    # SENSOR DISCOVERY
    # --------------------------------------------------------

    def discover_sensors(self):

        try:

            result = subprocess.run(
                ["termux-sensor", "-l"],
                capture_output=True,
                text=True,
                timeout=10
            )

            data = json.loads(result.stdout)

            sensors = data.get("sensors", [])

            self.sensor_names = sensors

        except Exception as e:

            print(f"[WARN] Sensor discovery failed: {e}")
            self.sensor_names = []

    # --------------------------------------------------------
    # SENSOR READING
    # --------------------------------------------------------

    def read_sensors(self):

        if not self.sensor_names:
            return {}

        try:

            # We deliberately use -n 1.
            # This prevents uncontrolled continuous API streams.
            result = subprocess.run(
                [
                    "termux-sensor",
                    "-a",
                    "-n",
                    "1"
                ],
                capture_output=True,
                text=True,
                timeout=8
            )

            if result.returncode != 0:
                return {}

            return json.loads(result.stdout)

        except Exception:
            return {}

    # --------------------------------------------------------
    # FEATURE EXTRACTION
    # --------------------------------------------------------

    def extract_features(self, data):

        features = []

        # ----------------------------------------------------
        # Helper
        # ----------------------------------------------------

        def get_values(key):

            obj = data.get(key)

            if not isinstance(obj, dict):
                return []

            values = obj.get("values", [])

            if not isinstance(values, list):
                return []

            return values

        # ----------------------------------------------------
        # ACCELEROMETER
        # ----------------------------------------------------

        acc = []

        for name in self.sensor_names:

            if "Accelerometer Non-wakeup" in name:
                acc = get_values(name)

                if len(acc) >= 3:
                    break

        for v in acc[:3]:
            features.append(normalize_value(v, 10.0))

        while len(features) < 3:
            features.append(0.0)

        # ----------------------------------------------------
        # GYROSCOPE
        # ----------------------------------------------------

        gyro = []

        for name in self.sensor_names:

            if (
                "Gyroscope Non-wakeup" in name
                and "Uncalibrated" not in name
            ):
                gyro = get_values(name)

                if len(gyro) >= 3:
                    break

        for v in gyro[:3]:
            features.append(normalize_value(v, 5.0))

        while len(features) < 6:
            features.append(0.0)

        # ----------------------------------------------------
        # MAGNETOMETER
        # ----------------------------------------------------

        mag = []

        for name in self.sensor_names:

            if (
                "Magnetometer Non-wakeup" in name
                and "Uncalibrated" not in name
            ):
                mag = get_values(name)

                if len(mag) >= 3:
                    break

        for v in mag[:3]:
            features.append(normalize_value(v, 100.0))

        while len(features) < 9:
            features.append(0.0)

        # ----------------------------------------------------
        # GRAVITY
        # ----------------------------------------------------

        gravity = []

        for name in self.sensor_names:

            if "gravity" in name.lower():

                gravity = get_values(name)

                if len(gravity) >= 3:
                    break

        for v in gravity[:3]:
            features.append(normalize_value(v, 10.0))

        while len(features) < 12:
            features.append(0.0)

        # ----------------------------------------------------
        # LINEAR ACCELERATION
        # ----------------------------------------------------

        linear = []

        for name in self.sensor_names:

            if "linear_acceleration" in name:

                linear = get_values(name)

                if len(linear) >= 3:
                    break

        for v in linear[:3]:
            features.append(normalize_value(v, 10.0))

        while len(features) < 15:
            features.append(0.0)

        # ----------------------------------------------------
        # LIGHT
        # ----------------------------------------------------

        light = []

        for name in self.sensor_names:

            lname = name.lower()

            if "light sensor" in lname or "lux" in lname:

                values = get_values(name)

                if values:
                    light = values
                    break

        features.append(
            normalize_value(
                light[0] if light else 0,
                1000.0
            )
        )

        # ----------------------------------------------------
        # PROXIMITY
        # ----------------------------------------------------

        prox = []

        for name in self.sensor_names:

            if "proximity" in name.lower():

                values = get_values(name)

                if values:
                    prox = values
                    break

        features.append(
            normalize_value(
                prox[0] if prox else 0,
                10.0
            )
        )

        # ----------------------------------------------------
        # PEDOMETER
        # ----------------------------------------------------

        steps = []

        for name in self.sensor_names:

            if "pedometer" in name.lower():

                values = get_values(name)

                if values:
                    steps = values
                    break

        features.append(
            normalize_value(
                steps[0] if steps else 0,
                10000.0
            )
        )

        # ----------------------------------------------------
        # ACTIVITY RECOGNITION
        # ----------------------------------------------------

        activity = []

        for name in self.sensor_names:

            if "activity_recognition" in name.lower():

                values = get_values(name)

                if values:
                    activity = values
                    break

        for v in activity[:4]:
            features.append(
                normalize_value(v, 5.0)
            )

        while len(features) < 23:
            features.append(0.0)

        # ----------------------------------------------------
        # ROTATION VECTOR
        # ----------------------------------------------------

        rotation = []

        for name in self.sensor_names:

            if "Rotation Vector" in name:

                rotation = get_values(name)

                if rotation:
                    break

        for v in rotation[:4]:
            features.append(
                normalize_value(v, 1.0)
            )

        while len(features) < 27:
            features.append(0.0)

        # ----------------------------------------------------
        # FIXED VECTOR
        # ----------------------------------------------------

        return [round(clamp(x), 6) for x in features[:27]]

    # --------------------------------------------------------
    # NEURONS
    # --------------------------------------------------------

    def new_neuron(self, prototype=None, parent=None):

        neuron_id = f"N{self.next_id}"
        self.next_id += 1

        if prototype is None:
            prototype = [
                random.random()
                for _ in range(27)
            ]

        neuron = {

            "id": neuron_id,

            "prototype": list(prototype),

            "cluster": self.choose_cluster(prototype),

            "confidence": 0.25,

            "fitness": 0.25,

            "age": 0,

            "parent": parent,

            "children": [],

            "activation_count": 0,

            "associated_memories": [],

            "previous_states": [],

            "next_states": [],

            "actions": [],

            "reward": 0.0,

            "wins": 0,

            "created_at": now(),

            "last_active": now()
        }

        self.neurons.append(neuron)

        if parent:

            for p in self.neurons:

                if p["id"] == parent:

                    if neuron_id not in p["children"]:
                        p["children"].append(neuron_id)

                    break

        self.created_total += 1

        return neuron

    def create_initial_neurons(self):

        for cluster in range(INITIAL_NEURONS):

            prototype = [
                random.random()
                for _ in range(27)
            ]

            n = self.new_neuron(prototype)

            n["cluster"] = cluster

    # --------------------------------------------------------
    # CLUSTER
    # --------------------------------------------------------

    def choose_cluster(self, prototype):

        if not self.neurons:
            return 0

        scores = {}

        for n in self.neurons:

            c = n["cluster"]

            d = distance(
                prototype,
                n["prototype"]
            )

            scores[c] = min(
                scores.get(c, 999),
                d
            )

        return min(
            scores,
            key=scores.get
        )

    # --------------------------------------------------------
    # WINNER
    # --------------------------------------------------------

    def find_winner(self, features):

        if not self.neurons:
            return None, 999

        best = None
        best_distance = 999

        for n in self.neurons:

            d = distance(
                features,
                n["prototype"]
            )

            if d < best_distance:

                best_distance = d
                best = n

        return best, best_distance

    # --------------------------------------------------------
    # LEARNING
    # --------------------------------------------------------

    def learn(self, neuron, features, d):

        if neuron is None:
            return

        neuron["age"] += 1
        neuron["activation_count"] += 1
        neuron["wins"] += 1

        neuron["last_active"] = now()

        # Adaptive learning.
        lr = LEARNING_RATE

        for i in range(
            min(
                len(neuron["prototype"]),
                len(features)
            )
        ):

            old = neuron["prototype"][i]
            target = features[i]

            neuron["prototype"][i] = (
                old + lr * (target - old)
            )

        # Confidence increases when matching improves.
        confidence_gain = 1.0 - clamp(d)

        neuron["confidence"] = clamp(
            0.90 * neuron["confidence"]
            + 0.10 * confidence_gain
        )

        # Fitness follows confidence + activation.
        activation_bonus = min(
            neuron["activation_count"] / 100.0,
            1.0
        )

        neuron["fitness"] = clamp(
            0.75 * neuron["confidence"]
            + 0.25 * activation_bonus
        )

    # --------------------------------------------------------
    # TEMPORAL MEMORY
    # --------------------------------------------------------

    def record_transition(self, previous, current):

        if not previous or not current:
            return

        if previous["id"] == current["id"]:
            return

        if current["id"] not in previous["next_states"]:
            previous["next_states"].append(
                current["id"]
            )

        if previous["id"] not in current["previous_states"]:
            current["previous_states"].append(
                previous["id"]
            )

        transition = {
            "from": previous["id"],
            "to": current["id"],
            "time": now()
        }

        self.transitions.append(transition)

    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    def save_memory(self, features, winner):

        if winner is None:
            return

        entry = {

            "time": now(),

            "neuron": winner["id"],

            "cluster": winner["cluster"],

            "features": list(features)
        }

        self.memory.append(entry)

        winner["associated_memories"].append(
            self.states_learned
        )

        # Prevent unlimited per-neuron memory IDs.
        if len(winner["associated_memories"]) > 100:
            winner["associated_memories"] = \
                winner["associated_memories"][-100:]

        self.memory_entries = len(self.memory)

    # --------------------------------------------------------
    # REWARD
    # --------------------------------------------------------

    def calculate_reward(self, distance_value, novelty):

        # Good recognition + useful novelty.
        recognition = 1.0 - clamp(distance_value)

        novelty_bonus = 0.20 if novelty else 0.0

        reward = (
            0.80 * recognition
            + novelty_bonus
        )

        return clamp(reward)

    # --------------------------------------------------------
    # NEUROGENESIS
    # --------------------------------------------------------

    def neurogenesis(self, features, winner, d):

        if len(self.neurons) >= MAX_NEURONS:
            return None

        # Create only when state is genuinely different.
        if d < NOVELTY_THRESHOLD:
            return None

        parent = winner["id"] if winner else None

        child = self.new_neuron(
            prototype=features,
            parent=parent
        )

        child["confidence"] = 0.40
        child["fitness"] = 0.40

        return child

    # --------------------------------------------------------
    # PRUNING
    # --------------------------------------------------------

    def prune(self):

        if len(self.neurons) <= INITIAL_NEURONS:
            return 0

        survivors = []
        removed = []

        for n in self.neurons:

            should_remove = (

                n["age"] > PRUNE_AFTER_AGE

                and n["fitness"] < MIN_FITNESS

                and n["activation_count"] < 3
            )

            if should_remove:
                removed.append(n)

            else:
                survivors.append(n)

        self.neurons = survivors

        for n in removed:

            self.pruned_total += 1

        return len(removed)

    # --------------------------------------------------------
    # STEP
    # --------------------------------------------------------

    def step(self):

        data = self.read_sensors()

        if not data:
            print(
                "WAITING FOR SENSOR DATA..."
            )

            return

        features = self.extract_features(data)

        winner, d = self.find_winner(features)

        novelty = d >= NOVELTY_THRESHOLD

        if winner:

            self.learn(
                winner,
                features,
                d
            )

        new_neuron = None

        if novelty:

            new_neuron = self.neurogenesis(
                features,
                winner,
                d
            )

        # If a new neuron was created, use it
        # immediately for the new state.
        active = new_neuron or winner

        if active:

            reward = self.calculate_reward(
                d,
                novelty
            )

            active["reward"] = (
                0.90 * active["reward"]
                + 0.10 * reward
            )

        if (
            self.previous_winner
            and active
        ):

            self.record_transition(
                self.previous_winner,
                active
            )

        self.save_memory(
            features,
            active
        )

        self.previous_state = features
        self.previous_winner = active

        self.states_learned += 1
        self.generation += 1

        pruned = 0

        if self.generation % 50 == 0:

            pruned = self.prune()

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        print(
            f"Gen {self.generation:5d} | "
            f"neurons={len(self.neurons):3d} | "
            f"winner={active['id'] if active else 'NONE'} | "
            f"distance={d:.4f} | "
            f"novelty={int(novelty)} | "
            f"confidence={active['confidence']:.3f} | "
            f"fitness={active['fitness']:.3f} | "
            f"reward={active['reward']:.3f} | "
            f"created={int(new_neuron is not None)} | "
            f"pruned={pruned}"
        )

        if new_neuron:

            print(
                f"  NEUROGENESIS: "
                f"{new_neuron['id']} "
                f"<- {winner['id'] if winner else 'ROOT'} "
                f"(new sensory state)"
            )

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    def save(self):

        os.makedirs(
            os.path.dirname(STATE_FILE),
            exist_ok=True
        )

        state = {

            "version": 2,

            "saved_at": now(),

            "generation": self.generation,

            "next_id": self.next_id,

            "created_total": self.created_total,

            "pruned_total": self.pruned_total,

            "states_learned": self.states_learned,

            "memory_entries": len(self.memory),

            "sensor_names": self.sensor_names,

            "neurons": self.neurons,

            "memory": list(self.memory),

            "transitions": list(self.transitions)
        }

        temp = STATE_FILE + ".tmp"

        with open(
            temp,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                state,
                f,
                indent=2
            )

        os.replace(
            temp,
            STATE_FILE
        )

    # --------------------------------------------------------
    # LOAD
    # --------------------------------------------------------

    def load(self):

        if not os.path.exists(STATE_FILE):
            return

        try:

            with open(
                STATE_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                state = json.load(f)

            self.generation = state.get(
                "generation",
                0
            )

            self.next_id = state.get(
                "next_id",
                0
            )

            self.created_total = state.get(
                "created_total",
                0
            )

            self.pruned_total = state.get(
                "pruned_total",
                0
            )

            self.states_learned = state.get(
                "states_learned",
                0
            )

            self.neurons = state.get(
                "neurons",
                []
            )

            self.memory = deque(
                state.get("memory", []),
                maxlen=MEMORY_LIMIT
            )

            self.transitions = deque(
                state.get("transitions", []),
                maxlen=TRANSITION_LIMIT
            )

            self.memory_entries = len(
                self.memory
            )

            print(
                f"[STATE] Loaded "
                f"{len(self.neurons)} neurons | "
                f"generation={self.generation}"
            )

        except Exception as e:

            print(
                f"[WARN] State load failed: {e}"
            )

    # --------------------------------------------------------
    # CHECKPOINT
    # --------------------------------------------------------

    def checkpoint(self):

        self.save()

        print()
        print("=" * 70)
        print("LIVE SENSOR BRAIN CHECKPOINT")
        print("=" * 70)
        print(
            f"Generation       : {self.generation}"
        )
        print(
            f"Live neurons     : {len(self.neurons)}"
        )
        print(
            f"Next neuron ID   : N{self.next_id}"
        )
        print(
            f"Created total    : {self.created_total}"
        )
        print(
            f"Pruned total     : {self.pruned_total}"
        )
        print(
            f"States learned   : {self.states_learned}"
        )
        print(
            f"Memory entries   : {len(self.memory)}"
        )
        print(
            f"Sensor features  : 27"
        )
        print("=" * 70)
        print()


# ============================================================
# MAIN
# ============================================================

brain = None


def stop_handler(signum, frame):

    global RUNNING

    RUNNING = False

    print()
    print("STOPPING SAFELY...")


def main():

    global brain

    signal.signal(
        signal.SIGINT,
        stop_handler
    )

    signal.signal(
        signal.SIGTERM,
        stop_handler
    )

    brain = SensorBrain()

    print()
    print("=" * 70)
    print("ANDROID LIVE SENSOR EVOLVING BRAIN v2")
    print("=" * 70)
    print(
        "TERMUX SENSOR API       : ON"
    )
    print(
        "FIXED SENSOR VECTOR     : 27"
    )
    print(
        "TEMPORAL MEMORY         : ON"
    )
    print(
        "PROTOTYPE LEARNING      : ON"
    )
    print(
        "NOVELTY DETECTION       : ON"
    )
    print(
        "NEUROGENESIS            : ON"
    )
    print(
        "LINEAGE                 : ON"
    )
    print(
        "REWARD / FITNESS        : ON"
    )
    print(
        "PERSISTENT MEMORY       : ON"
    )
    print(
        f"MAX NEURONS             : {MAX_NEURONS}"
    )
    print("=" * 70)
    print()

    last_checkpoint = time.monotonic()

    try:

        while RUNNING:

            brain.step()

            # Checkpoint every ~30 seconds.
            if (
                time.monotonic()
                - last_checkpoint
                >= 30
            ):

                brain.checkpoint()

                last_checkpoint = (
                    time.monotonic()
                )

            time.sleep(
                SAMPLE_DELAY
            )

    finally:

        if brain:

            brain.save()

            print()
            print(
                f"SAVED: {STATE_FILE}"
            )

            print(
                f"FINAL NEURONS: "
                f"{len(brain.neurons)}"
            )

            print(
                f"TOTAL CREATED: "
                f"{brain.created_total}"
            )

            print(
                f"TOTAL PRUNED: "
                f"{brain.pruned_total}"
            )

            print(
                "BRAIN CHECKPOINT SAVED."
            )


if __name__ == "__main__":
    main()

