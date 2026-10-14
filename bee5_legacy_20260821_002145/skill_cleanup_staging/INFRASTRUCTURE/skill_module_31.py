import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (module_name text, description text)''')
    conn.commit()
    conn.close()

def add_skill_module(module_name, description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills VALUES (?,?)", (module_name, description))
    conn.commit()
    conn.close()

def main():
    module_name = 'skill_module_31'
    description = 'This is a new skill module.'
    create_table()
    add_skill_module(module_name, description)

if __name__ == '__main__':
    main()