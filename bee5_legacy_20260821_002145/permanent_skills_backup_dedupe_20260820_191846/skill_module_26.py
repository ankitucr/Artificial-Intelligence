import os
import sqlite3

def get_active_skills():
    active_skills = os.listdir()
    if '__pycache__' in active_skills:
        active_skills.remove('__pycache__')
    return active_skills

def update_skill_status(skill_name, status):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS skill_status (skill_name text, status text)")
    c.execute("INSERT OR REPLACE INTO skill_status VALUES (?, ?)", (skill_name, status))
    conn.commit()
    conn.close()

def get_skill_status(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT status FROM skill_status WHERE skill_name=?", (skill_name,))
    status = c.fetchone()
    conn.close()
    if status:
        return status[0]
    else:
        return None

active_skills = get_active_skills()
for skill in active_skills:
    if skill.endswith('.py'):
        update_skill_status(skill, 'active')
    else:
        update_skill_status(skill, 'inactive')

for skill in active_skills:
    print(f"{skill}: {get_skill_status(skill)}")