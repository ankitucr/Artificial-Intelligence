import os
import json
import re
import numpy as np
from collections import Counter

class SubconsciousMemory:
    def __init__(self, memory_file="src/memory/memory_bank.json", threshold=0.85):
        self.memory_file = memory_file
        self.threshold = threshold
        self.memories = []
        self._load_memory()

    def _load_memory(self):
        """Loads previous experiences from the local JSON brain."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    self.memories = json.load(f)
                print(f"🧠 Subconscious loaded with {len(self.memories)} neural patterns.")
            except json.JSONDecodeError:
                self.memories = []
        else:
            self.memories = []
            self._save_memory()

    def _save_memory(self):
        """Saves current experiences to storage."""
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        with open(self.memory_file, 'w') as f:
            json.dump(self.memories, f, indent=4)

    def _tokenize(self, text):
        """Cleans and breaks text into tokens (Bag of Words) for math operations."""
        # Convert to lowercase and extract words/numbers
        words = re.findall(r'\w+', text.lower())
        return Counter(words)

    def _cosine_similarity(self, vec1, vec2):
        """Uses Numpy for lightning-fast Cosine Similarity between two text vectors."""
        intersection = set(vec1.keys()) & set(vec2.keys())
        
        # Calculate dot product
        numerator = sum([vec1[x] * vec2[x] for x in intersection])

        # Calculate magnitudes
        sum1 = sum([val**2 for val in vec1.values()])
        sum2 = sum([val**2 for val in vec2.values()])
        denominator = np.sqrt(sum1) * np.sqrt(sum2)

        if not denominator:
            return 0.0
        return float(numerator) / denominator

    def remember(self, error_signature, solution_ast, description):
        """Saves a new solved problem into the subconscious."""
        new_memory = {
            "error": error_signature,
            "solution": solution_ast,
            "description": description
        }
        self.memories.append(new_memory)
        self._save_memory()
        print(f"💾 New pattern permanently wired into Subconscious: '{description}'")

    def recall(self, current_error):
        """Searches the subconscious for a similar past error to avoid API calls."""
        if not self.memories:
            return None

        current_vector = self._tokenize(current_error)
        best_match = None
        highest_score = 0.0

        for memory in self.memories:
            memory_vector = self._tokenize(memory["error"])
            score = self._cosine_similarity(current_vector, memory_vector)

            if score > highest_score:
                highest_score = score
                best_match = memory

        if highest_score >= self.threshold:
            print(f"⚡ SUBCONSCIOUS REFLEX TRIGGERED! (Match: {highest_score*100:.1f}%)")
            print(f"   ↳ Bypassing API. Using known solution for: {best_match['description']}")
            return best_match["solution"]
        
        return None

# ==========================================
# Testing the Subconscious Engine
# ==========================================
if __name__ == "__main__":
    print("\n🚀 Booting Subconscious Engine (Numpy Vector Math)...\n")
    brain = SubconsciousMemory()

    # 1. Simulate Pika solving a problem using an API (Cost: High)
    print("--- Training Phase ---")
    brain.remember(
        error_signature="TypeError: Cannot read properties of undefined (reading 'length') at line 42",
        solution_ast="if (myVar && myVar.length) { ... }",
        description="Handled undefined length property"
    )

    # 2. Simulate the SAME error happening again (Cost: 0 API Calls)
    print("\n--- Testing Exact Match ---")
    result = brain.recall("TypeError: Cannot read properties of undefined (reading 'length') at line 42")
    
    # 3. Simulate a SLIGHTLY DIFFERENT error (e.g., different line number)
    print("\n--- Testing Semantic Fuzzy Match ---")
    # Pika should recognize this is basically the same issue despite line 89 instead of 42
    result_fuzzy = brain.recall("TypeError: Cannot read properties of undefined (reading 'length') at line 89")
    
    # 4. Simulate a COMPLETELY UNKNOWN error
    print("\n--- Testing Unknown Error ---")
    result_unknown = brain.recall("SyntaxError: Unexpected token '{' at line 12")
    if not result_unknown:
        print("🤷‍♂️ Pattern unknown. Pika needs to route this to the Mega Load-Balancer (APIs).")
