import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (name text, description text)''')
    conn.commit()
    conn.close()

def add_skill_to_database(skill_module_name, description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills VALUES (?, ?)", (skill_module_name, description))
    conn.commit()
    conn.close()

def main():
    create_table()
    skill_module_name = "skill_module_37"
    description = "This is a skill module"
    add_skill_to_database(skill_module_name, description)

if __name__ == "__main__":
    main()