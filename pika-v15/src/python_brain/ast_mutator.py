import libcst as cst
import os


class FunctionReplacer(cst.CSTTransformer):
    def __init__(self, target_func_name, new_func_code):
        self.target_func_name = target_func_name
        self.found = False  # 👈 tracks whether the target actually existed
        new_tree = cst.parse_module(new_func_code)
        self.new_node = new_tree.body[0]

    def leave_FunctionDef(self, original_node, updated_node):
        if original_node.name.value == self.target_func_name:
            self.found = True
            print(f"  --> 🛠️ AST Surgeon: Replacing function '{self.target_func_name}'...")
            return self.new_node
        return updated_node


def mutate_code(file_path, func_name, new_code):
    """
    Returns True if the file was actually mutated (function replaced OR newly
    added), False if nothing changed or the mutation failed. The caller
    (pika_core.py's analyze_and_fix) relies on this to know whether to trust
    the fix at all — silently doing nothing used to be reported as success.
    """
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    # 1. Validate the new code is at least syntactically parseable BEFORE
    #    touching the file — an API hallucination shouldn't corrupt working code.
    try:
        cst.parse_module(new_code)
    except Exception as e:
        print(f"❌ AST Surgeon: Generated code is not valid Python, aborting mutation. ({e})")
        return False

    with open(file_path, 'r') as f:
        source_code = f.read()

    try:
        tree = cst.parse_module(source_code)
    except Exception as e:
        print(f"❌ AST Surgeon: Existing file has invalid syntax, cannot safely mutate. ({e})")
        return False

    transformer = FunctionReplacer(func_name, new_code)
    modified_tree = tree.visit(transformer)

    if transformer.found:
        with open(file_path, 'w') as f:
            f.write(modified_tree.code)
        print("  ✅ Mutation Successful! Existing function replaced (formatting and comments preserved).")
        return True

    # 2. Function didn't exist yet -> this is Pika GROWING a new skill,
    #    not fixing an old one. Append it instead of silently doing nothing.
    print(f"  ℹ️ AST Surgeon: '{func_name}' not found in file — treating this as a NEW skill, appending it.")
    try:
        new_module_tree = cst.parse_module(new_code)
        appended_body = list(tree.body) + list(new_module_tree.body)
        grown_tree = tree.with_changes(body=appended_body)
        with open(file_path, 'w') as f:
            f.write(grown_tree.code)
        print(f"  ✅ Mutation Successful! New function '{func_name}' grown and appended.")
        return True
    except Exception as e:
        print(f"❌ AST Surgeon: Failed to append new function: {e}")
        return False


# ==========================================
# Testing the AST Surgeon
# ==========================================
if __name__ == "__main__":
    print("\n🚀 Booting Pika AST Surgeon...\n")

    test_file = "dummy_test.py"
    with open(test_file, 'w') as f:
        f.write("# Yeh ek important comment hai jo delete nahi hona chahiye\n"
                 "def bad_function():\n"
                 "    print('Error: Yeh code fail ho jayega')\n"
                 "    return False\n\n"
                 "def good_function():\n"
                 "    print('Yeh theek hai')\n")

    print("--- 📄 Original File Before Mutation ---")
    with open(test_file, 'r') as f:
        print(f.read())

    fixed_code_from_api = (
        "def bad_function():\n"
        "    # Fixed by Pika v15\n"
        "    print('Success: Code successfully fixed by AST Surgeon!')\n"
        "    return True\n"
    )

    print("\n--- ⚡ Test 1: Replacing an EXISTING function ---")
    ok1 = mutate_code(test_file, "bad_function", fixed_code_from_api)
    print(f"  mutate_code returned: {ok1}")

    print("\n--- ⚡ Test 2: Growing a BRAND NEW function (didn't exist before) ---")
    new_skill_code = (
        "def brand_new_skill(x):\n"
        "    # Grown autonomously by Pika\n"
        "    return x * 2\n"
    )
    ok2 = mutate_code(test_file, "brand_new_skill", new_skill_code)
    print(f"  mutate_code returned: {ok2}")

    print("\n--- ⚡ Test 3: Garbage/invalid code from a bad API response ---")
    ok3 = mutate_code(test_file, "bad_function", "def bad_function(:\n  this is not python")
    print(f"  mutate_code returned: {ok3} (should be False, file should be untouched)")

    print("\n--- 📄 File After All Mutations ---")
    with open(test_file, 'r') as f:
        print(f.read())

    os.remove(test_file)
    print("\n🏁 AST Diagnostics Complete.\n")
