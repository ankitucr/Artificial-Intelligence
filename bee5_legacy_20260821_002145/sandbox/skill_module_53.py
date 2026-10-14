import sqlite3

def create_active_skills_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS active_skills (
                id INTEGER PRIMARY KEY,
                filename TEXT,
                status TEXT
                )""")
    conn.commit()
    conn.close()

def update_active_skills(filename):
    create_active_skills_table()
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO active_skills (filename, status) VALUES (?,?)", (filename, 'active'))
    conn.commit()
    conn.close()

update_active_skills('skill_module_53.py')