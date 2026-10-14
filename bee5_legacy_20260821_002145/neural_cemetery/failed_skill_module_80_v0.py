# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_80.py", line 33, in <module>
    new_skill.save_to_db()
    ~~~~~~~~~~~~~~~~~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_80.py", line 15, in save_to_db
    c.execute("INSERT INTO micro_skills VALUES (?,?,?)", (self.name, self.description, hashed_id))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table micro_skills has 2 columns but 3 values were supplied


import sqlite3
import hashlib

class MicroSkill:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def save_to_db(self):
        conn = sqlite3.connect('shared_memory.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS micro_skills
                     (name text, description text, id text)""")
        hashed_id = hashlib.sha256((self.name + self.description).encode()).hexdigest()
        c.execute("INSERT INTO micro_skills VALUES (?,?,?)", (self.name, self.description, hashed_id))
        conn.commit()
        conn.close()

    @staticmethod
    def get_skills_from_db():
        conn = sqlite3.connect('shared_memory.db')
        c = conn.cursor()
        c.execute("SELECT * FROM micro_skills")
        skills = c.fetchall()
        conn.close()
        return skills

class WebScraper:
    def __init__(self, url):
        self.url = url

new_skill = MicroSkill('web_scraper', 'a basic web scraper to read from duckduckgo')
new_skill.save_to_db()

print(MicroSkill.get_skills_from_db())