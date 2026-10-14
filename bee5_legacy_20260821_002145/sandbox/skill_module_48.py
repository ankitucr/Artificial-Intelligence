import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                unique_id TEXT,
                skill_name TEXT
                )""")
    conn.commit()
    conn.close()

def add_skill_to_database(unique_id, skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills (unique_id, skill_name) VALUES (?,?)", (unique_id, skill_name))
    conn.commit()
    conn.close()

def main():
    create_table()
    unique_id = "12345"
    skill_name = "Python Programming"
    add_skill_to_database(unique_id, skill_name)

if __name__ == "__main__":
    main()