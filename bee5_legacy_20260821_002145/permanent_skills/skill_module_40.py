import sqlite3
import os

def create_skill_module(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (name text, status text)''')
    c.execute("INSERT INTO skills VALUES (?, ?)", (skill_name, "active"))
    conn.commit()
    conn.close()

def create_new_skill(skill_name):
    new_skill_module = f"skill_module_{skill_name}.py"
    with open(new_skill_module, "w") as f:
        f.write(f"# {skill_name} micro-skill\n")
        f.write("import requests\n")
        f.write("def execute_skill(query):\n")
        f.write("    url = 'https://api.duckduckgo.com/?q=' + query + '&format=json'\n")
        f.write("    response = requests.get(url)\n")
        f.write("    return response.json()\n")
    create_skill_module(new_skill_module)

create_new_skill("duckduckgo_reader")