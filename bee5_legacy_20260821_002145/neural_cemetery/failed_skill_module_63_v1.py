# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_63.py", line 24, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_63.py", line 20, in main
    insert_new_skill(conn, "neural_networks_skill", data)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_63.py", line 13, in insert_new_skill
    c.execute("INSERT OR REPLACE INTO skills (name, data) VALUES (?,?)", (skill_name, str(skill_data)))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has no column named data


import sqlite3

def create_table(conn):
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills (
                name text PRIMARY KEY,
                data text
                )""")
    conn.commit()

def insert_new_skill(conn, skill_name, skill_data):
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO skills (name, data) VALUES (?,?)", (skill_name, str(skill_data)))
    conn.commit()

def main():
    conn = sqlite3.connect('shared_memory.db')
    create_table(conn)
    data = "This is some sample data"
    insert_new_skill(conn, "neural_networks_skill", data)
    conn.close()

if __name__ == "__main__":
    main()