import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills
                 (skill_name text, skill_type text)""")
    conn.commit()
    conn.close()

def add_micro_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills VALUES (?, ?)", (skill_name, 'micro'))
    conn.commit()
    conn.close()

def main():
    create_table()
    add_micro_skill('web_search')

if __name__ == "__main__":
    main()