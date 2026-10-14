import os
import json
import re
import math
import time
import numpy as np
from collections import Counter
from load_balancer import AI_LoadBalancer
from ast_mutator import mutate_code  # 👈 AST Surgeon Integrated!


class PikaNeuralCore:
    """
    Pika's self-evolving brain.

    Flow for every problem:
      1. Vectorize the prompt (TF-IDF weighted, not raw word count)
      2. Search existing neurons for the closest match
      3. decide() picks one of three autonomous actions:
           - REUSE   : confidence is high enough, use memory, skip API
           - ASK_API : confidence too low / neuron has a bad track record, escalate
           - FLAG    : neuron matched but has failed too often before -> don't trust it,
                       treat as unknown and go to API anyway
      4. Whatever solution is used, outcome is recorded back into memory
         (record_outcome) so the neuron's trust score evolves over time.
      5. consolidate() periodically merges near-duplicate neurons so the
         brain doesn't bloat with 50 versions of the same fix.
    """

    def __init__(self, brain_file="src/python_brain/neural_vectors.json", skills_file=None):
        self.brain_file = brain_file
        # skills_file: path to pika_skills.py — the growing library of self-written
        # functions. If given, think() will automatically check this library
        # BEFORE calling any API, and automatically wire a successful match
        # back into memory as a new neuron. Fully automatic, no manual imports.
        self.skills_file = skills_file
        self._skill_index = []
        # Base threshold - this is now a STARTING point, not fixed.
        # Each neuron's effective threshold shifts based on its own track record.
        self.base_confidence_threshold = 0.85
        self.neurons = []
        self.doc_freq = Counter()   # for TF-IDF across all stored neurons
        self.total_docs = 0
        self.stats = {"api_calls_saved": 0, "api_calls_made": 0, "fixes_applied": 0, "fixes_failed": 0,
                       "skill_library_reuses": 0}
        self.load_brain()
        if self.skills_file:
            self._index_skill_library()

    # ------------------------------------------------------------------
    # PERSISTENCE
    # ------------------------------------------------------------------
    def load_brain(self):
        """Pika ke existing neurons (skills/vectors) ko load karta hai."""
        default_stats = {"api_calls_saved": 0, "api_calls_made": 0, "fixes_applied": 0, "fixes_failed": 0,
                          "skill_library_reuses": 0}
        if os.path.exists(self.brain_file):
            try:
                with open(self.brain_file, 'r') as f:
                    payload = json.load(f)
                    # backward compatible: old files were just a raw list
                    if isinstance(payload, list):
                        self.neurons = payload
                        self.stats = default_stats
                    else:
                        self.neurons = payload.get("neurons", [])
                        # merge instead of replace — an older brain file saved
                        # before a new stat key existed shouldn't crash on that
                        # key later. Old values are kept, missing keys are filled in.
                        loaded_stats = payload.get("stats", {})
                        self.stats = {**default_stats, **loaded_stats}
                self._rebuild_doc_freq()
                print(f"🧠 [Pika Core] Booted up. Current Neural Capacity: {len(self.neurons)} skills.")
            except json.JSONDecodeError:
                self.neurons = []
                self.stats = default_stats
        else:
            self.neurons = []
            self.stats = default_stats
            self.save_brain()

    def save_brain(self):
        """Naye seekhe hue skills ko JSON me as a Vector save karta hai."""
        dir_name = os.path.dirname(self.brain_file)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        payload = {"neurons": self.neurons, "stats": self.stats}
        with open(self.brain_file, 'w') as f:
            json.dump(payload, f, indent=4)

    # ------------------------------------------------------------------
    # VECTORIZATION (TF-IDF instead of raw counts -> much better matching)
    # ------------------------------------------------------------------
    def _rebuild_doc_freq(self):
        self.doc_freq = Counter()
        self.total_docs = len(self.neurons)
        for n in self.neurons:
            for word in set(n.get("raw_words", [])):
                self.doc_freq[word] += 1

    def vectorize(self, text, register=False):
        """Text ko TF-IDF weighted vector me convert karta hai."""
        words = re.findall(r'\w+', str(text).lower())
        tf = Counter(words)
        vec = {}
        total_docs = max(self.total_docs, 1)
        for word, count in tf.items():
            df = self.doc_freq.get(word, 0) + 1  # +1 smoothing
            idf = math.log((total_docs + 1) / df) + 1
            vec[word] = count * idf
        if register:
            return vec, words
        return vec

    def cosine_similarity(self, vec1, vec2):
        intersection = set(vec1.keys()) & set(vec2.keys())
        numerator = sum([vec1[x] * vec2[x] for x in intersection])
        sum1 = sum([val ** 2 for val in vec1.values()])
        sum2 = sum([val ** 2 for val in vec2.values()])
        denominator = math.sqrt(sum1) * math.sqrt(sum2)
        if not denominator:
            return 0.0
        return float(numerator) / denominator

    # ------------------------------------------------------------------
    # AUTONOMOUS DECISION LAYER
    # ------------------------------------------------------------------
    def _effective_threshold(self, neuron):
        """
        Neuron ka apna track record dekh ke uska trust-adjusted threshold nikalta hai.
        Zyada fails wale neuron ko harder banate hain (usse easily trust nahi karenge).
        Zyada successes wale neuron ko thoda lenient bana dete hain.
        """
        success = neuron.get("success_count", 0)
        fail = neuron.get("fail_count", 0)
        base = self.base_confidence_threshold

        if fail == 0 and success == 0:
            return base
        total = success + fail
        reliability = success / total  # 0..1

        if reliability >= 0.8:
            return max(base - 0.10, 0.60)   # trusted neuron, lower bar
        elif reliability <= 0.4:
            return min(base + 0.10, 0.97)   # unreliable neuron, raise bar hard
        return base

    def find_best_match(self, current_vector, context_type):
        best_match = None
        highest_score = 0.0
        for neuron in self.neurons:
            if neuron.get("type") != context_type:
                continue
            score = self.cosine_similarity(current_vector, neuron.get("vector", {}))
            if score > highest_score:
                highest_score = score
                best_match = neuron
        return best_match, highest_score

    def decide(self, best_match, score):
        """
        Pika khud yahan faisla leta hai — koi hardcoded 'if user says X' nahi.
        Returns one of: 'REUSE', 'ASK_API'
        """
        if best_match is None:
            return "ASK_API", "no matching neuron exists yet"

        threshold = self._effective_threshold(best_match)

        if score >= threshold:
            return "REUSE", f"score {score:.2f} >= trust-adjusted threshold {threshold:.2f}"
        else:
            return "ASK_API", f"score {score:.2f} < trust-adjusted threshold {threshold:.2f}"

    # ------------------------------------------------------------------
    # AUTOMATIC SKILL-LIBRARY REUSE
    # (This is what makes the brain compound: every problem solved by an
    #  existing skill gets wired back into memory as a new neuron — the
    #  more skills get used, the more new neurons form, with zero manual
    #  wiring from outside code.)
    # ------------------------------------------------------------------
    def _index_skill_library(self):
        """Reads pika_skills.py and builds a lightweight vector index of
        every function's name + docstring, so we can match new problems
        against skills Pika has already grown."""
        self._skill_index = []
        if not self.skills_file or not os.path.exists(self.skills_file):
            return
        try:
            import ast
            with open(self.skills_file, 'r') as f:
                source = f.read()
            tree = ast.parse(source)
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    doc = ast.get_docstring(node) or ""
                    args = [a.arg for a in node.args.args]
                    text = f"{node.name} {doc}"
                    vec = self.vectorize(text)
                    self._skill_index.append({
                        "name": node.name, "doc": doc, "args": args, "vector": vec
                    })
        except Exception as e:
            print(f"⚠️ [Skill Library] Could not index {self.skills_file}: {e}")

    def _build_cross_file_skill_call(self, skill_name, target_name):
        """
        Generates a wrapper for use in a REAL project file (not pika_skills.py
        itself) that calls an existing grown skill. Uses an absolute-path
        dynamic import so it works regardless of where the target file lives
        in the project — this is the mechanism that makes skills genuinely
        USED by real bug-fixes, instead of sitting unused in pika_skills.py.
        """
        abs_path = os.path.abspath(self.skills_file) if self.skills_file else "src/skills/pika_skills.py"
        return (
            f"def {target_name}(*args, **kwargs):\n"
            f"    \"\"\"Auto-wired: reuses Pika's existing '{skill_name}' skill.\"\"\"\n"
            f"    import importlib.util as _ilu\n"
            f"    _spec = _ilu.spec_from_file_location('pika_skills', r'{abs_path}')\n"
            f"    _mod = _ilu.module_from_spec(_spec)\n"
            f"    _spec.loader.exec_module(_mod)\n"
            f"    return _mod.{skill_name}(*args, **kwargs)\n"
        )

    def _extract_defined_func_name(self, code):
        """Returns the name of the first top-level function actually defined
        in a code snippet, or None if there isn't one (e.g. a comment-only
        'already exists' stub)."""
        m = re.search(r'^def\s+(\w+)\s*\(', code, flags=re.MULTILINE)
        return m.group(1) if m else None

    def _rename_top_level_function(self, code, new_name):
        """
        Renames the first top-level `def <old_name>(` in a code snippet to
        `def <new_name>(`. Used when a reused solution's function name
        doesn't match what the current caller actually needs — a plain text
        substitution is safe here because every solution in this pipeline
        is a single self-contained function body.
        """
        import re
        return re.sub(r'^def\s+\w+\s*\(', f'def {new_name}(', code, count=1, flags=re.MULTILINE)

    def _extract_target_func_name(self, prompt):
        """
        Both callers (evolve.py's skill-writing prompt and bridge.py's
        error-fix prompt) embed the intended function name in a predictable
        pattern. Extracting it lets REUSE_SKILL wire a correctly-named
        function instead of a generic stand-in that AST Surgeon can't match.
        """
        import re
        m = re.search(r"function named '([a-zA-Z_][a-zA-Z0-9_]*)'", prompt)
        if m:
            return m.group(1)
        m = re.search(r"inside function: '([a-zA-Z_][a-zA-Z0-9_]*)'", prompt)
        if m:
            return m.group(1)
        return None

    def find_reusable_skill(self, prompt, threshold=0.30):
        """
        Checks the growing skill library for something close enough to
        reuse instead of calling an API. Threshold is lower than neuron
        matching because skill docstrings are short/sparse compared to
        full error logs.
        """
        if self.skills_file:
            self._index_skill_library()  # always fresh — evolve.py may have just grown a new one
        if not self._skill_index:
            return None, 0.0

        current_vector = self.vectorize(prompt)
        best, best_score = None, 0.0
        for skill in self._skill_index:
            score = self.cosine_similarity(current_vector, skill["vector"])
            if score > best_score:
                best_score = score
                best = skill
        if best_score >= threshold:
            return best, best_score
        return None, 0.0

    # ------------------------------------------------------------------
    # MAIN THINK LOOP
    # ------------------------------------------------------------------
    def think(self, prompt, context_type="error_fix"):
        """THE MAIN LOGIC GATE: Sochta hai, khud decide karta hai, aur code generate karta hai."""
        print(f"\n⚡ [Pika Core] Analyzing input...")
        current_vector, raw_words = self.vectorize(prompt, register=True)

        best_match, score = self.find_best_match(current_vector, context_type)
        action, reason = self.decide(best_match, score)

        if action == "REUSE":
            # Verify the stored solution ACTUALLY defines the function name
            # this call needs. Earlier versions blindly renamed a matched
            # neuron's function to fit — but renaming only fixes the LABEL,
            # not the underlying logic, which stays whatever the original
            # (possibly unrelated) match was for. That produced functions
            # like slugify() that were secretly flatten_dict()'s body with
            # a new name — wrong logic that still passed self-test (which
            # only checks "doesn't crash", not "does the right thing").
            #
            # Now: only reuse from memory if the name already matches
            # exactly. A name mismatch means this isn't a safe reuse —
            # fall through to the API instead of faking a fit.
            target_name = self._extract_target_func_name(prompt)
            stored_name = self._extract_defined_func_name(best_match.get("solution", ""))

            if target_name and stored_name and target_name != stored_name:
                print(f"🟡 [Decision] Memory match found but name mismatch "
                      f"('{stored_name}' stored vs '{target_name}' needed) — "
                      f"NOT reusing (would be wrong logic under a new name). Asking API instead.")
            else:
                print(f"🟢 [Decision: REUSE] {reason}. Bypassing APIs.")
                self.stats["api_calls_saved"] += 1
                best_match["last_used"] = time.time()
                best_match["times_used"] = best_match.get("times_used", 0) + 1
                self.save_brain()
                return best_match["solution"], False, best_match

        # NEW: before ever hitting an API, check if a skill Pika already grew
        # (via the self-evolution loop) already covers this. If so, wire it
        # into a brand-new neuron automatically — no manual import, no
        # outside code involved. This is how the brain compounds itself.
        #
        # Threshold is deliberately HIGH (0.82) because short docstrings are
        # prone to false positives: generic words ("returns", "value",
        # "error", "fallback") can push unrelated skills (e.g. a retry
        # decorator vs a file-reading helper) above a looser threshold,
        # producing a skill that runs without crashing but does the WRONG
        # thing — worse than just writing a fresh one via the API.
        skill, skill_score = self.find_reusable_skill(prompt, threshold=0.82)
        if skill:
            target_name = self._extract_target_func_name(prompt)

            if context_type == "skill_growth":
                # Growing pika_skills.py ITSELF — cross-name reuse here would
                # mean self-importing, which is unsafe/broken. Only reuse
                # under the exact same name (see earlier fix).
                if target_name and target_name != skill["name"]:
                    print(f"🟡 [Decision] Skill library match found ('{skill['name']}') but it's "
                          f"for a different name than needed ('{target_name}') — not reusing. Asking API.")
                else:
                    print(f"🧩 [Decision: REUSE_SKILL] '{skill['name']}' already exists exactly as "
                          f"needed (match {skill_score:.2f}). Wiring it into memory, skipping API.")
                    solution = f"# '{skill['name']}' already exists in pika_skills.py — reused as-is, no changes needed.\n"
                    self.stats["api_calls_saved"] += 1
                    self.stats["skill_library_reuses"] += 1
                    new_neuron = self.grow_neuron(prompt, current_vector, raw_words, solution, context_type)
                    return solution, False, new_neuron
            else:
                # Fixing a REAL project file — pika_skills.py is a genuine
                # external dependency here, so calling into it (even under a
                # different function name) is safe and correct. THIS is what
                # makes skills actually get used in real code, not just sit
                # in pika_skills.py unused.
                name_to_define = target_name or skill["name"]
                print(f"🧩 [Decision: REUSE_SKILL] Reusing existing skill '{skill['name']}' "
                      f"(match {skill_score:.2f}) to fix real code as '{name_to_define}'. Skipping API.")
                solution = self._build_cross_file_skill_call(skill["name"], name_to_define)
                self.stats["api_calls_saved"] += 1
                self.stats["skill_library_reuses"] += 1
                new_neuron = self.grow_neuron(prompt, current_vector, raw_words, solution, context_type)
                return solution, False, new_neuron

        print(f"🔴 [Decision: ASK_API] {reason}. Waking up Mega Load-Balancer...")
        lb = AI_LoadBalancer()
        role = "debugger" if context_type == "error_fix" else "coder"

        strict_prompt = (f"{prompt}\n\nIMPORTANT: Return ONLY the raw valid Python code for the function. "
                          f"No markdown, no backticks, no explanations. Just the code.")

        api_solution = lb.ask(strict_prompt, role=role)
        clean_solution = re.sub(r'`{1,3}(python|javascript)?', '', api_solution).strip()

        self.stats["api_calls_made"] += 1

        # Validate syntax BEFORE memorizing — an invalid solution provides
        # zero future value and, if saved, would keep getting matched by
        # REUSE for unrelated future prompts, failing every single time
        # (this was silently happening before this check existed).
        try:
            import ast as _ast_check
            _ast_check.parse(clean_solution)
        except SyntaxError as e:
            print(f"⚠️ [Pika Core] API returned invalid Python syntax ({e}) — "
                  f"not memorizing this as a neuron, returning as one-off attempt only.")
            return clean_solution, True, None

        new_neuron = self.grow_neuron(prompt, current_vector, raw_words, clean_solution, context_type)

        return clean_solution, True, new_neuron

    # ------------------------------------------------------------------
    # LEARNING / GROWTH
    # ------------------------------------------------------------------
    def grow_neuron(self, prompt, vector, raw_words, solution, context_type):
        """Naya vector database me inject karna — ek naya skill paida hota hai."""
        new_neuron = {
            "id": f"n_{int(time.time() * 1000)}",
            "type": context_type,
            "original_prompt": prompt,
            "vector": vector,
            "raw_words": raw_words,
            "solution": solution,
            "success_count": 0,
            "fail_count": 0,
            "times_used": 0,
            "created_at": time.time(),
            "last_used": time.time(),
        }
        self.neurons.append(new_neuron)
        self.doc_freq.update(set(raw_words))
        self.total_docs += 1
        self.save_brain()
        print(f"💾 [Neuroplasticity] New skill acquired and wired into Neural Core! "
              f"(Total skills: {len(self.neurons)})")
        return new_neuron

    def record_outcome(self, neuron, success: bool):
        """
        External caller (bridge.py / auto_runner.js via bridge) reports back
        whether the applied solution actually worked. This is what makes
        Pika reinforcement-learn instead of blindly trusting its own memory.
        """
        if neuron is None:
            return
        if success:
            neuron["success_count"] = neuron.get("success_count", 0) + 1
            self.stats["fixes_applied"] += 1
            print(f"✅ [Reinforcement] Neuron '{neuron.get('id')}' confirmed working. "
                  f"Trust increased ({neuron['success_count']} wins / {neuron.get('fail_count', 0)} fails).")
        else:
            neuron["fail_count"] = neuron.get("fail_count", 0) + 1
            self.stats["fixes_failed"] += 1
            print(f"⚠️ [Reinforcement] Neuron '{neuron.get('id')}' failed in practice. "
                  f"Trust decreased ({neuron.get('success_count', 0)} wins / {neuron['fail_count']} fails).")
        self.save_brain()

    # ------------------------------------------------------------------
    # SELF-MAINTENANCE (sleep-like consolidation)
    # ------------------------------------------------------------------
    def consolidate(self, similarity_threshold=0.95, min_fail_ratio_to_prune=0.75, min_attempts_to_prune=4):
        """
        Periodically call this (e.g. once a day / once per N think() calls) so
        the brain doesn't bloat and doesn't keep trusting consistently-bad neurons.

        - Merges near-duplicate neurons (keeps the one with better track record)
        - Prunes neurons that have failed way more than they've succeeded
        """
        pruned = 0
        merged = 0

        # 1. Prune chronically failing neurons
        survivors = []
        for n in self.neurons:
            attempts = n.get("success_count", 0) + n.get("fail_count", 0)
            if attempts >= min_attempts_to_prune:
                fail_ratio = n.get("fail_count", 0) / attempts
                if fail_ratio >= min_fail_ratio_to_prune:
                    pruned += 1
                    continue
            survivors.append(n)
        self.neurons = survivors

        # 2. Merge near-duplicates (same type, very high cosine similarity)
        merged_list = []
        used = set()
        for i, n1 in enumerate(self.neurons):
            if i in used:
                continue
            cluster = [n1]
            for j in range(i + 1, len(self.neurons)):
                if j in used:
                    continue
                n2 = self.neurons[j]
                if n2.get("type") != n1.get("type"):
                    continue
                sim = self.cosine_similarity(n1.get("vector", {}), n2.get("vector", {}))
                if sim >= similarity_threshold:
                    cluster.append(n2)
                    used.add(j)
            if len(cluster) > 1:
                # keep the most reliable one in the cluster
                best = max(cluster, key=lambda n: n.get("success_count", 0) - n.get("fail_count", 0))
                merged_list.append(best)
                merged += len(cluster) - 1
            else:
                merged_list.append(n1)
        self.neurons = merged_list

        self._rebuild_doc_freq()
        self.save_brain()
        print(f"🧹 [Consolidation] Pruned {pruned} unreliable neurons, merged {merged} duplicates. "
              f"Brain size now: {len(self.neurons)} skills.")
        return {"pruned": pruned, "merged": merged, "remaining": len(self.neurons)}

    def report(self):
        """Quick health/status snapshot of the brain."""
        if self.skills_file:
            self._index_skill_library()  # refresh so the count reflects this cycle's mutation too
        total_attempts = self.stats["api_calls_saved"] + self.stats["api_calls_made"]
        savings_pct = (self.stats["api_calls_saved"] / total_attempts * 100) if total_attempts else 0
        print("\n📊 [Pika Brain Report]")
        print(f"   Total neurons        : {len(self.neurons)}")
        print(f"   Skills in library    : {len(self._skill_index)}")
        print(f"   API calls saved      : {self.stats['api_calls_saved']}")
        print(f"   API calls made       : {self.stats['api_calls_made']}")
        print(f"   Memory hit rate      : {savings_pct:.1f}%")
        print(f"   Skill library reuses : {self.stats['skill_library_reuses']}")
        print(f"   Fixes confirmed good : {self.stats['fixes_applied']}")
        print(f"   Fixes confirmed bad  : {self.stats['fixes_failed']}")
        return self.stats

    # ------------------------------------------------------------------
    # HIGH-LEVEL ACTION (unchanged interface, now feedback-aware)
    # ------------------------------------------------------------------
    def analyze_and_fix(self, file_path, func_name, error_log):
        """Pika ek hi baar me error read karta hai, sochta hai, aur file fix kar deta hai."""
        print(f"\n[Pika Action] Initiating Auto-Fix for '{func_name}' in {os.path.basename(file_path)}")

        prompt = f"Fix this error: '{error_log}' inside function: '{func_name}'."
        solution_code, used_api, neuron = self.think(prompt, context_type="error_fix")

        try:
            mutated = mutate_code(file_path, func_name, solution_code)
            if not mutated:
                # AST Surgeon refused/failed to touch the file (invalid code,
                # bad target, etc). This is NOT a success — don't lie to the caller.
                print(f"❌ [Pika Action] AST Surgeon could not apply the mutation.")
                if neuron:
                    self.record_outcome(neuron, success=False)
                return {"status": "failed", "error": "mutation_rejected_by_ast_surgeon",
                        "neuron_id": neuron.get("id") if neuron else None}

            print(f"✅ [Pika Action] File successfully mutated by AST Surgeon.")
            # NOTE: we still don't yet know if the fix actually resolves the crash —
            # the caller (auto_runner.js re-running the file) is what proves that.
            # Call record_outcome(neuron, True/False) once the re-run result is known.
            return {"status": "success", "used_api": used_api, "neuron_id": neuron.get("id") if neuron else None}
        except Exception as e:
            print(f"❌ [Pika Action] AST Mutation Failed: {e}")
            if neuron:
                self.record_outcome(neuron, success=False)
            return {"status": "failed", "error": str(e)}


# ==========================================
# TEST THE FULL AUTONOMOUS + SELF-LEARNING CORE
# ==========================================
if __name__ == "__main__":
    test_file = "neural_test.py"
    with open(test_file, "w") as f:
        f.write("def broken_math(a, b):\n    return a / b # Will cause division by zero\n")

    core = PikaNeuralCore(brain_file="neural_vectors_test.json")

    print("\n=== FIRST RUN (should hit API, no memory yet) ===")
    result1 = core.analyze_and_fix(
        file_path=test_file,
        func_name="broken_math",
        error_log="ZeroDivisionError: division by zero"
    )
    # Simulate the outer system confirming the fix worked
    neuron1 = next((n for n in core.neurons if n["id"] == result1.get("neuron_id")), None)
    core.record_outcome(neuron1, success=True)

    # Re-break the file so we can test memory reuse
    with open(test_file, "w") as f:
        f.write("def broken_math(a, b):\n    return a / b # Will cause division by zero\n")

    print("\n=== SECOND RUN (same error, should hit MEMORY not API) ===")
    result2 = core.analyze_and_fix(
        file_path=test_file,
        func_name="broken_math",
        error_log="ZeroDivisionError: division by zero"
    )

    core.report()
    core.consolidate()

    os.remove(test_file)
    if os.path.exists("neural_vectors_test.json"):
        os.remove("neural_vectors_test.json")
