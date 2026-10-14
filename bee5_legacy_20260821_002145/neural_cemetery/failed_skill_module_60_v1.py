# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_60.py", line 16, in <module>
    add_micro_skill('web_search')
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_60.py", line 12, in add_micro_skill
    c.execute("INSERT INTO micro_skills (skill_name) VALUES (?)", (skill_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table micro_skills has no column named skill_name


import sqlite3

conn = sqlite3.connect('shared_memory.db')
c = conn.cursor()

def create_micro_skills_table():
    c.execute("""CREATE TABLE IF NOT EXISTS micro_skills
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, skill_name TEXT)""")
    conn.commit()

def add_micro_skill(skill_name):
    c.execute("INSERT INTO micro_skills (skill_name) VALUES (?)", (skill_name,))
    conn.commit()

create_micro_skills_table()
add_micro_skill('web_search')
conn.close()