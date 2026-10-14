# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_74.py", line 23, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_74.py", line 21, in main
    add_skill(new_skill)
    ~~~~~~~~~^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_74.py", line 15, in add_skill
    c.execute("INSERT INTO skills (skill_name) VALUES (?)", (skill_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has no column named skill_name


import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (id INTEGER PRIMARY KEY, skill_name TEXT)''')
    conn.commit()
    conn.close()

def add_skill(skill_name):
    create_table()
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills (skill_name) VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()

def main():
    new_skill = "new_skill"
    add_skill(new_skill)

main()