# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_60.py", line 19, in <module>
    add_micro_skill('web_search')
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_60.py", line 15, in add_micro_skill
    c.execute("INSERT INTO micro_skills (skill_name) VALUES (?)", (skill_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table micro_skills has no column named skill_name


import sqlite3

def create_micro_skills_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS micro_skills
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, skill_name text)''')
    conn.commit()
    conn.close()

def add_micro_skill(skill_name):
    create_micro_skills_table()
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO micro_skills (skill_name) VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()

add_micro_skill('web_search')