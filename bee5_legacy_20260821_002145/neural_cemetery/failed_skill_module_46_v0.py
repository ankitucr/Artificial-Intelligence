# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_46.py", line 48, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_46.py", line 45, in main
    update_active_skills(skill_file_name)
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_46.py", line 36, in update_active_skills
    c.execute("INSERT INTO active_skills VALUES (?)", (skill,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table active_skills has 2 columns but 1 values were supplied


import sqlite3
import os

def create_micro_skill(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS micro_skills
                 (name text, description text)''')
    conn.commit()
    c.execute("INSERT INTO micro_skills VALUES (?,?)",
              (skill_name, skill_description))
    conn.commit()
    conn.close()

def generate_skill_module(skill_name):
    skill_file_name = f"skill_module_{skill_name}.py"
    with open(skill_file_name, "w") as f:
        f.write(f"# {skill_name} micro-skill\n")
        f.write("def skill_function():\n")
        f.write("    # implement micro-skill functionality here\n")
        f.write("    pass\n")
    return skill_file_name

def update_active_skills(skill_file_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS active_skills
                 (file_name text)''')
    conn.commit()
    c.execute("SELECT * FROM active_skills")
    active_skills = [row[0] for row in c.fetchall()]
    active_skills.append(skill_file_name)
    c.execute("DELETE FROM active_skills")
    conn.commit()
    for skill in active_skills:
        c.execute("INSERT INTO active_skills VALUES (?)", (skill,))
        conn.commit()
    conn.close()

def main():
    skill_name = "wiki_info"
    skill_description = "fetch information from wikipedia"
    create_micro_skill(skill_name, skill_description)
    skill_file_name = generate_skill_module(skill_name)
    update_active_skills(skill_file_name)

if __name__ == "__main__":
    main()