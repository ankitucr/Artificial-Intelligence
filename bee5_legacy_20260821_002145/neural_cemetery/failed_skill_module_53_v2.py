# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_53.py", line 22, in <module>
    update_active_skills('skill_module_53.py')
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_53.py", line 18, in update_active_skills
    c.execute("INSERT INTO active_skills (filename, status) VALUES (?,?)", (filename, 'active'))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table active_skills has no column named filename


import sqlite3

def create_active_skills_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS active_skills (
                id INTEGER PRIMARY KEY,
                filename TEXT,
                status TEXT
                )""")
    conn.commit()
    conn.close()

def update_active_skills(filename):
    create_active_skills_table()
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO active_skills (filename, status) VALUES (?,?)", (filename, 'active'))
    conn.commit()
    conn.close()

update_active_skills('skill_module_53.py')