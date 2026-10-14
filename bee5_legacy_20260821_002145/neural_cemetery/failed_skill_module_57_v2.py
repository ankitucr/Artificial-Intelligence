# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_57.py", line 18, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_57.py", line 15, in main
    register_skill_module(filename)
    ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_57.py", line 9, in register_skill_module
    c.execute("INSERT OR IGNORE INTO skills (filename) VALUES (?)", (filename,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has no column named filename


import sqlite3

def register_skill_module(filename):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills (
                filename TEXT PRIMARY KEY
                )""")
    c.execute("INSERT OR IGNORE INTO skills (filename) VALUES (?)", (filename,))
    conn.commit()
    conn.close()

def main():
    filename = __file__
    register_skill_module(filename)

if __name__ == "__main__":
    main()