import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY,
                skill_module_name TEXT
                )""")
    conn.commit()
    conn.close()

def add_skill_to_database(skill_module_name):
    create_table()
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills (skill_module_name) VALUES (?)", (skill_module_name,))
    conn.commit()
    conn.close()

def main():
    skill_module_name = "skill_module_49"
    add_skill_to_database(skill_module_name)

if __name__ == "__main__":
    main()