# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_53.py", line 20, in <module>
    update_active_skills(filename)
    ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_53.py", line 7, in update_active_skills
    c.execute("INSERT INTO active_skills (filename, status) VALUES (?,?)", (filename, 'active'))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table active_skills has no column named filename


import sqlite3
import os

def update_active_skills(filename):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO active_skills (filename, status) VALUES (?,?)", (filename, 'active'))
    conn.commit()
    conn.close()

def get_active_skills():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT filename FROM active_skills")
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows]

filename = os.path.basename(__file__)
update_active_skills(filename)