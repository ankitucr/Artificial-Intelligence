# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_66.py", line 35, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_66.py", line 30, in main
    save_data('test_key', 'test_value')
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_66.py", line 15, in save_data
    c.execute("INSERT INTO bee5_data VALUES (?,?)", (key, value))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.IntegrityError: datatype mismatch


import sqlite3
import time

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bee5_data
                 (key text, value text)''')
    conn.commit()
    conn.close()

def save_data(key, value):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO bee5_data VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()

def read_data(key):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT value FROM bee5_data WHERE key=?", (key,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def main():
    start_time = time.time()
    create_table()
    save_data('test_key', 'test_value')
    print(read_data('test_key'))
    print("Execution time: {:.2f} seconds".format(time.time() - start_time))

if __name__ == "__main__":
    main()