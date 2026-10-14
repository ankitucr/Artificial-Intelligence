import sqlite3

def update_active_skills(skill_file_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS active_skills (skill_file_name TEXT PRIMARY KEY, status TEXT)")
    c.execute("INSERT OR REPLACE INTO active_skills VALUES (?,?)", (skill_file_name, 'active'))
    conn.commit()
    conn.close()

def main():
    skill_file_name = "skill_module_46.py"
    update_active_skills(skill_file_name)

if __name__ == "__main__":
    main()