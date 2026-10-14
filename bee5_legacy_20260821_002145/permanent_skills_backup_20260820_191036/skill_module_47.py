import sqlite3
import os
import hashlib

def create_skill_module(skill_name):
    connection = sqlite3.connect('shared_memory.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM skills WHERE name=?', (skill_name,))
    if cursor.fetchone():
        connection.close()
        return False
    skill_id = str(hashlib.sha256(skill_name.encode()).hexdigest())
    cursor.execute('INSERT INTO skills (name, id) VALUES (?,?)', (skill_name, skill_id))
    connection.commit()
    connection.close()
    with open(f'skill_module_{skill_id}.py', 'w') as f:
        f.write(f'def {skill_name}():\n    pass')
    return True

def main():
    skill_name = 'duckduckgo_reader'
    if create_skill_module(skill_name):
        print(f'Skill module {skill_name} created successfully')
    else:
        print(f'Skill module {skill_name} already exists')

if __name__ == '__main__':
    main()