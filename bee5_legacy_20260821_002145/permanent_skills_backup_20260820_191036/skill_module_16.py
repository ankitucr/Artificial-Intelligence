import sqlite3
import time

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS bee5
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, data TEXT)''')
    conn.commit()
    conn.close()

def insert_data(data):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO bee5 (data) VALUES (?)", (data,))
    conn.commit()
    conn.close()

def read_data():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM bee5")
    rows = c.fetchall()
    conn.close()
    return rows

create_table()
insert_data('initial data')
print(read_data())