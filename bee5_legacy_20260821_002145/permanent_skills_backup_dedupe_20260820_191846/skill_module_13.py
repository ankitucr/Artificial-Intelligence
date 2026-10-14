import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills (
                skill_name text,
                skill_description text
                )""")
    conn.commit()
    conn.close()

def add_skill(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills VALUES (?, ?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def main():
    create_table()
    new_skill_name = "Python Programming"
    new_skill_description = "A high-level programming language"
    add_skill(new_skill_name, new_skill_description)

if __name__ == "__main__":
    main()