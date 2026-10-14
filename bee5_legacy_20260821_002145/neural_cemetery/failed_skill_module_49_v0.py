# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_49.py", line 49, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_49.py", line 44, in main
    add_skill_to_database(skill_module_name)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_49.py", line 17, in add_skill_to_database
    c.execute("INSERT INTO skills VALUES (?)", (skill_module_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has 2 columns but 1 values were supplied


import sqlite3
import os
import hashlib

def create_skill_module(skill_name, skill_code):
    skill_hash = hashlib.sha256(skill_name.encode()).hexdigest()
    skill_module_name = f"skill_module_{skill_hash}.py"
    with open(skill_module_name, "w") as f:
        f.write(skill_code)
    return skill_module_name

def add_skill_to_database(skill_module_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (module_name text)''')
    c.execute("INSERT INTO skills VALUES (?)", (skill_module_name,))
    conn.commit()
    conn.close()

def get_active_skills():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (module_name text)''')
    c.execute("SELECT * FROM skills")
    active_skills = [row[0] for row in c.fetchall()]
    conn.close()
    return active_skills

def main():
    skill_name = "neural_network_node"
    skill_code = """
import numpy as np

class NeuralNetworkNode:
    def __init__(self):
        self.weights = np.random.rand(10)

    def forward(self, input):
        return np.dot(input, self.weights)
"""
    skill_module_name = create_skill_module(skill_name, skill_code)
    add_skill_to_database(skill_module_name)
    active_skills = get_active_skills()
    print(active_skills)

if __name__ == "__main__":
    main()