import importlib.util
import sqlite3
import os

def connect_to_db():
    conn = sqlite3.connect('shared_memory.db')
    return conn

def create_table(conn):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, value text)''')
    conn.commit()

def main():
    conn = connect_to_db()
    create_table(conn)
    conn.close()

if __name__ == "__main__":
    main()