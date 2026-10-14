# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_50.py", line 39, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_50.py", line 31, in main
    micro_skill.save_to_db()
    ~~~~~~~~~~~~~~~~~~~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_50.py", line 19, in save_to_db
    cursor.execute('INSERT INTO skills VALUES (?,?,?)', (self.skill_id, self.skill_name, self.skill_description))
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has 2 columns but 3 values were supplied


import sqlite3
import hashlib
import os
import requests

class MicroSkill:
    def __init__(self, skill_name, skill_description):
        self.skill_name = skill_name
        self.skill_description = skill_description
        self.skill_id = self.generate_skill_id()

    def generate_skill_id(self):
        return hashlib.sha256((self.skill_name + self.skill_description).encode()).hexdigest()

    def save_to_db(self):
        conn = sqlite3.connect('shared_memory.db')
        cursor = conn.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS skills (skill_id TEXT, skill_name TEXT, skill_description TEXT)')
        cursor.execute('INSERT INTO skills VALUES (?,?,?)', (self.skill_id, self.skill_name, self.skill_description))
        conn.commit()
        conn.close()

    def fetch_data(self, url):
        response = requests.get(url)
        return response.text

def main():
    skill_name = 'skill_module_text_summarizer'
    skill_description = 'A micro-skill to summarize text from a given URL'
    micro_skill = MicroSkill(skill_name, skill_description)
    micro_skill.save_to_db()
    print(f'Skill ID: {micro_skill.skill_id}')

    url = 'https://example.com/article'
    summary = micro_skill.fetch_data(url)
    print(summary)

if __name__ == '__main__':
    main()