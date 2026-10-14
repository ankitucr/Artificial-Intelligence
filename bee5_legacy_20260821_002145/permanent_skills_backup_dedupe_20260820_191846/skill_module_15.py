import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name text)''')
    conn.commit()
    conn.close()

def add_micro_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills (name) VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()

def get_micro_skills():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skills")
    rows = c.fetchall()
    conn.close()
    return rows

create_table()
new_skill = "example_skill"
add_micro_skill(new_skill)
print(get_micro_skills())