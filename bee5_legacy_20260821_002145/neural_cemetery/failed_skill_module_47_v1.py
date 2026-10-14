# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_47.py", line 24, in <module>
    add_wikipedia_skill()
    ~~~~~~~~~~~~~~~~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_47.py", line 22, in add_wikipedia_skill
    create_skill_module('wikipedia', 'a skill for searching wikipedia')
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_47.py", line 16, in create_skill_module
    c.execute("INSERT INTO skills (name, description) VALUES (?,?)", (skill_name, skill_description))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has no column named description


import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS skills
        (name TEXT PRIMARY KEY, description TEXT)
    ''')
    conn.commit()
    conn.close()

def create_skill_module(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills (name, description) VALUES (?,?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def add_wikipedia_skill():
    create_table()
    create_skill_module('wikipedia', 'a skill for searching wikipedia')

add_wikipedia_skill()