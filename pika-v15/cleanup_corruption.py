"""
cleanup_corruption.py — one-time fix for the self-referential import bug.

Removes:
  1. Any neuron in neural_vectors.json whose stored solution contains
     'from pika_skills import ...' (these are permanently broken —
     reusing them will always fail self-test).
  2. Any function in pika_skills.py that contains that same broken import
     line (these block the WHOLE file from importing, which fails every
     self-test after them, even for perfectly good new skills).

Run once:
    python cleanup_corruption.py

Safe to run even if there's nothing to clean — it just reports 0 removed.
"""

import json
import os
import re

BRAIN_FILE = "src/python_brain/neural_vectors.json"
SKILLS_FILE = "src/skills/pika_skills.py"


def clean_neurons():
    if not os.path.exists(BRAIN_FILE):
        print(f"⚠️  {BRAIN_FILE} not found, skipping.")
        return

    with open(BRAIN_FILE, "r") as f:
        payload = json.load(f)

    neurons = payload.get("neurons", []) if isinstance(payload, dict) else payload
    before = len(neurons)

    clean_list = [
        n for n in neurons
        if "from pika_skills import" not in n.get("solution", "")
    ]
    removed = before - len(clean_list)

    if isinstance(payload, dict):
        payload["neurons"] = clean_list
    else:
        payload = clean_list

    with open(BRAIN_FILE, "w") as f:
        json.dump(payload, f, indent=4)

    print(f"🧠 Neurons: removed {removed} corrupted (self-import) neuron(s). "
          f"{before} -> {len(clean_list)} remaining.")


def clean_skills_file():
    if not os.path.exists(SKILLS_FILE):
        print(f"⚠️  {SKILLS_FILE} not found, skipping.")
        return

    with open(SKILLS_FILE, "r") as f:
        source = f.read()

    # Split into top-level blocks (functions + leading comments), find any
    # block containing the bad self-import line, and drop just that block.
    # Functions in this file are always separated by a blank line before 'def'.
    blocks = re.split(r'\n(?=def )', source)

    kept_blocks = []
    removed_count = 0
    for block in blocks:
        if "from pika_skills import" in block:
            removed_count += 1
            # try to report which function name got dropped, for visibility
            m = re.search(r'^def\s+(\w+)\s*\(', block, flags=re.MULTILINE)
            name = m.group(1) if m else "<unknown>"
            print(f"   🗑️  Removed corrupted function: '{name}'")
            continue
        kept_blocks.append(block)

    new_source = "\n".join(kept_blocks)

    with open(SKILLS_FILE, "w") as f:
        f.write(new_source)

    print(f"📄 Skills file: removed {removed_count} corrupted function(s) from {SKILLS_FILE}.")


if __name__ == "__main__":
    print("🧹 Starting corruption cleanup...\n")
    clean_neurons()
    clean_skills_file()
    print("\n✅ Done. Safe to run `python evolve.py` again now.")
