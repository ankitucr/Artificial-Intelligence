import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills (
                skill_name text,
                skill_status text
                )""")
    conn.commit()
    conn.close()

def add_micro_skill(skill_name):
    create_table()
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills VALUES (?, ?)", (skill_name, 'active'))
    conn.commit()
    conn.close()

def get_skills():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skills")
    skills = c.fetchall()
    conn.close()
    return skills

add_micro_skill('web_scraper')
print(get_skills())