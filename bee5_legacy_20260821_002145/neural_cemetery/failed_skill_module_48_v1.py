# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_48.py", line 25, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_48.py", line 22, in main
    add_skill_to_database(unique_id, skill_name)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_48.py", line 14, in add_skill_to_database
    c.execute("INSERT INTO skills (unique_id, skill_name) VALUES (?,?)", (unique_id, skill_name))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has no column named unique_id


import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills
                (unique_id text, skill_name text)""")
    conn.commit()
    conn.close()

def add_skill_to_database(unique_id, skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills (unique_id, skill_name) VALUES (?,?)", (unique_id, skill_name))
    conn.commit()
    conn.close()

def main():
    create_table()
    unique_id = "12345"
    skill_name = "example_skill"
    add_skill_to_database(unique_id, skill_name)

if __name__ == "__main__":
    main()