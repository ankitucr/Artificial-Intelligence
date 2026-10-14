# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_49.py", line 26, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_49.py", line 23, in main
    add_skill_to_database(skill_module_name)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_49.py", line 17, in add_skill_to_database
    c.execute("INSERT INTO skills (skill_module_name) VALUES (?)", (skill_module_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has no column named skill_module_name


import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY,
                skill_module_name TEXT
                )""")
    conn.commit()
    conn.close()

def add_skill_to_database(skill_module_name):
    create_table()
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills (skill_module_name) VALUES (?)", (skill_module_name,))
    conn.commit()
    conn.close()

def main():
    skill_module_name = "skill_module_49"
    add_skill_to_database(skill_module_name)

if __name__ == "__main__":
    main()