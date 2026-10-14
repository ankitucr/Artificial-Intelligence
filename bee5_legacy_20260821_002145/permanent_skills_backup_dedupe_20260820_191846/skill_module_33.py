import sqlite3
import requests
from bs4 import BeautifulSoup

class MicroSkill:
    def __init__(self):
        self.conn = sqlite3.connect('shared_memory.db')
        self.cursor = self.conn.cursor()

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS micro_skills
            (id INTEGER PRIMARY KEY, name TEXT, description TEXT)
        ''')
        self.conn.commit()

    def add_micro_skill(self, name, description):
        self.cursor.execute('INSERT INTO micro_skills (name, description) VALUES (?,?)', (name, description))
        self.conn.commit()

    def fetch_info(self, topic):
        url = f'https://duckduckgo.com/html/?q={topic}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        info = soup.find_all('a', class_='result__a')
        return [i.text for i in info]

    def add_info(self, topic):
        info = self.fetch_info(topic)
        self.add_micro_skill(topic, ', '.join(info))

    def close_connection(self):
        self.conn.close()

if __name__ == '__main__':
    micro_skill = MicroSkill()
    micro_skill.create_table()
    micro_skill.add_info('basic_neural_network')
    micro_skill.close_connection()