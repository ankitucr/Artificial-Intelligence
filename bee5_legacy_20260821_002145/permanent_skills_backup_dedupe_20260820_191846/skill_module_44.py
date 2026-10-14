import sqlite3

def create_table():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (module_id text, skill_info text)''')
    conn.commit()
    conn.close()

def add_skill_to_db(module_name, skill_name, skill_description):
    create_table()
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('INSERT INTO skills VALUES (?,?)', (module_name.split('_')[2].split('.')[0], f"{skill_name}:{skill_description}"))
    conn.commit()
    conn.close()

def main():
    module_name = "skill_module_44.py"
    skill_name = "new_skill"
    skill_description = "this is a new skill"
    add_skill_to_db(module_name, skill_name, skill_description)

if __name__ == "__main__":
    main()