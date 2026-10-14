import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS micro_skills (
                id INTEGER PRIMARY KEY,
                name TEXT,
                description TEXT
                )""")
    conn.commit()
    conn.close()

def insert_skill(new_skill_name, new_skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO micro_skills (name, description) VALUES (?,?)", (new_skill_name, new_skill_description))
    conn.commit()
    conn.close()

def get_all_skills():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM micro_skills")
    skills = c.fetchall()
    conn.close()
    return skills

def update_skill(skill_id, new_skill_name, new_skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("UPDATE micro_skills SET name =?, description =? WHERE id =?", (new_skill_name, new_skill_description, skill_id))
    conn.commit()
    conn.close()

create_table()
new_skill_name = "Test Skill"
new_skill_description = "This is a test skill"
insert_skill(new_skill_name, new_skill_description)
skills = get_all_skills()
for skill in skills:
    print(skill)