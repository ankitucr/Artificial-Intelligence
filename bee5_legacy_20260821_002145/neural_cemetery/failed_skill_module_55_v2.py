# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_55.py", line 38, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_55.py", line 30, in main
    insert_data(1, 'Hello World')
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_55.py", line 16, in insert_data
    cursor.execute('INSERT INTO data (id, info) VALUES (?, ?)', (id, text))
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table data has no column named info


import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS data
        (id INTEGER PRIMARY KEY, info TEXT)
    ''')
    conn.commit()
    conn.close()

def insert_data(id, text):
    conn = sqlite3.connect('shared_memory.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO data (id, info) VALUES (?, ?)', (id, text))
    conn.commit()
    conn.close()

def select_data(id):
    conn = sqlite3.connect('shared_memory.db')
    cursor = conn.cursor()
    cursor.execute('SELECT info FROM data WHERE id = ?', (id,))
    result = cursor.fetchone()
    conn.close()
    return result

def main():
    create_table()
    insert_data(1, 'Hello World')
    result = select_data(1)
    if result:
        print(result[0])
    else:
        print('No data found')

if __name__ == '__main__':
    main()