import sqlite3
import os

def create_skill_module(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skill_modules
                 (name text, description text)""")
    c.execute("INSERT INTO skill_modules VALUES (?, ?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def generate_skill_module_code(skill_name):
    code = f"""
import sqlite3

def {skill_name}():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skill_modules WHERE name=?", ({skill_name},))
    result = c.fetchone()
    conn.close()
    return result

{skill_name}()
"""
    with open(f"skill_module_{skill_name}.py", "w") as f:
        f.write(code)

def main():
    skill_name = "duckduckgo_search"
    skill_description = "Searches DuckDuckGo for a given query"
    create_skill_module(skill_name, skill_description)
    generate_skill_module_code(skill_name)

if __name__ == "__main__":
    main()