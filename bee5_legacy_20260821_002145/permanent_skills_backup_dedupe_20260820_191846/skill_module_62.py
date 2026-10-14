import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS micro_skills
        (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)
    ''')
    conn.commit()
    conn.close()

def add_micro_skill(skill_name):
    create_table()
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO micro_skills (name) VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()
    return skill_name

def add_skill(new_skill):
    add_micro_skill(new_skill)
    return new_skill

def get_skills():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT name FROM micro_skills")
    skills = c.fetchall()
    conn.close()
    return skills

create_table()
new_skill = "Test Skill"
print(add_skill(new_skill))
print(get_skills())