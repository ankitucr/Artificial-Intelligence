import sqlite3

def create_database():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (name text PRIMARY KEY, description text)''')
    conn.commit()
    conn.close()

def create_skill_module(skill_name, skill_description):
    create_database()
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO skills (name, description) VALUES (?,?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def add_wikipedia_skill():
    create_skill_module('wikipedia', 'a skill for searching wikipedia')

create_database()
add_wikipedia_skill()