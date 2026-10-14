import sqlite3
import os

def create_micro_skill(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS micro_skills (
                skill_name text,
                skill_description text
                )""")
    c.execute("INSERT INTO micro_skills VALUES (?,?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def write_skill_module(skill_name, skill_code):
    filename = f"skill_module_{skill_name}.py"
    with open(filename, 'w') as f:
        f.write(skill_code)

def main():
    skill_name = "web_search"
    skill_description = "Searches for information on duckduckgo"
    skill_code = f"""
import duckduckgo
def search(query):
    return duckduckgo.get_zci(query)
"""
    create_micro_skill(skill_name, skill_description)
    write_skill_module(skill_name, skill_code)

if __name__ == "__main__":
    main()