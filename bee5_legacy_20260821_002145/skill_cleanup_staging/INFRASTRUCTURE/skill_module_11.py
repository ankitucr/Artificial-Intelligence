import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills (
                skill_name text,
                description text
                )""")
    conn.commit()
    conn.close()

def add_micro_skill(skill_name, description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills VALUES (?,?)", (skill_name, description))
    conn.commit()
    conn.close()

def main():
    create_table()
    new_skill_name = "new_skill"
    new_skill_description = "new skill description"
    add_micro_skill(new_skill_name, new_skill_description)

if __name__ == "__main__":
    main()