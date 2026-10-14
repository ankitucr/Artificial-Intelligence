import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills
                (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)""")
    conn.commit()
    conn.close()

def add_micro_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills (name) VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()

def main():
    create_table()
    new_skill = "Skill 1"
    add_micro_skill(new_skill)

if __name__ == "__main__":
    main()