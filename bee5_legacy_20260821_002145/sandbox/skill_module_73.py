import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, skill_name text)''')
    conn.commit()
    conn.close()

def add_skill(skill_name):
    create_table()
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills (skill_name) VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()

def main():
    create_table()
    new_skill = "bee_ai_skill"
    add_skill(new_skill)

if __name__ == "__main__":
    main()