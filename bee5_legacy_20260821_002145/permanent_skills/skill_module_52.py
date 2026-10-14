import sqlite3
import requests
import json

class NewSkill:
    def __init__(self):
        self.conn = sqlite3.connect('shared_memory.db')
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS quotes
            (id INTEGER PRIMARY KEY AUTOINCREMENT, quote TEXT)
        ''')
        self.conn.commit()

    def get_quote(self):
        response = requests.get('https://zenquotes.io/api/random')
        return response.json()[0]

    def save_quote(self, quote):
        self.cursor.execute('INSERT INTO quotes (quote) VALUES (?)', (quote['q'],))
        self.conn.commit()

    def load_quote(self):
        self.cursor.execute('SELECT quote FROM quotes ORDER BY RANDOM() LIMIT 1')
        return self.cursor.fetchone()

    def close_connection(self):
        self.conn.close()

def main():
    new_skill = NewSkill()
    new_skill.create_table()
    quote = new_skill.get_quote()
    new_skill.save_quote(quote)
    loaded_quote = new_skill.load_quote()
    print(loaded_quote)
    new_skill.close_connection()

if __name__ == '__main__':
    main()