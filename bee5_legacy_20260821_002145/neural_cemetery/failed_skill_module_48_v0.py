# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_48.py", line 46, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_48.py", line 42, in main
    add_skill_to_database(unique_id, skill_name)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_48.py", line 21, in add_skill_to_database
    c.execute("INSERT INTO skills (id, name) VALUES (?,?)", (skill_id, skill_name))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has no column named id


import sqlite3
import hashlib

def generate_unique_skill_id():
    import time
    import random
    random_id = str(time.time()) + str(random.randint(1, 1000000))
    unique_id = str(int(hashlib.sha256(random_id.encode()).hexdigest(), 16))
    return unique_id

def create_skill_module(unique_id, skill_name, skill_function):
    with open(f"skill_module_{unique_id}.py", "w") as f:
        f.write(f"# {skill_name} Micro-Skill\n")
        f.write(f"def {skill_name}():\n")
        f.write(f"    {skill_function}\n")
    return f"skill_module_{unique_id}.py"

def add_skill_to_database(skill_id, skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills (id, name) VALUES (?,?)", (skill_id, skill_name))
    conn.commit()
    conn.close()

def get_skill_id_from_database(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT id FROM skills WHERE name=?", (skill_name,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0]
    else:
        return None

def main():
    unique_id = generate_unique_skill_id()
    skill_name = "basic_neural_network_node"
    skill_function = "print('Basic Neural Network Node') # TODO: implement"
    new_skill_module = create_skill_module(unique_id, skill_name, skill_function)
    print(f"Created new skill module: {new_skill_module}")
    add_skill_to_database(unique_id, skill_name)
    print(f"Added {skill_name} to database with id: {unique_id}")

if __name__ == "__main__":
    main()