# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_62.py", line 26, in <module>
    print(add_skill(new_skill))
          ~~~~~~~~~^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_62.py", line 21, in add_skill
    add_micro_skill(new_skill)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_62.py", line 16, in add_micro_skill
    c.execute("INSERT OR IGNORE INTO micro_skills (skill_name) VALUES (?)", (skill_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table micro_skills has no column named skill_name


import sqlite3

def create_tables():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS micro_skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name text
                )""")
    conn.commit()
    conn.close()

def add_micro_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO micro_skills (skill_name) VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()

def add_skill(new_skill):
    add_micro_skill(new_skill)
    return f"Skill '{new_skill}' added"

create_tables()
new_skill = "Python Programming"
print(add_skill(new_skill))