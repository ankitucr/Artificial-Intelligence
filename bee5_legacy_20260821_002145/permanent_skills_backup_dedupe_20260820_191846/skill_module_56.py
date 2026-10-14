import sqlite3
import random
import string

class SkillModule:
    def __init__(self, name):
        self.name = name
        self.conn = sqlite3.connect('shared_memory.db')
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS words
            (id INTEGER PRIMARY KEY, word TEXT)
        ''')
        self.conn.commit()

    def add_word(self, word):
        self.cursor.execute('INSERT INTO words (word) VALUES (?)', (word,))
        self.conn.commit()

    def get_word(self):
        self.cursor.execute('SELECT word FROM words ORDER BY RANDOM() LIMIT 1')
        return self.cursor.fetchone()

    def close_connection(self):
        self.conn.close()

def generate_skill_module_name():
    return 'skill_module_' + ''.join(random.choices(string.ascii_letters + string.digits, k=16)) + '.py'

def create_skill_module():
    name = generate_skill_module_name()
    module = SkillModule(name)
    module.create_table()
    module.add_word('Hello, world!')
    word = module.get_word()
    print(word)
    module.close_connection()

create_skill_module()