import sqlite3

def register_skill_module(filename):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills (
                filename TEXT PRIMARY KEY
                )""")
    c.execute("INSERT OR IGNORE INTO skills (filename) VALUES (?)", (filename,))
    conn.commit()
    conn.close()

def main():
    filename = __file__
    register_skill_module(filename)

if __name__ == "__main__":
    main()