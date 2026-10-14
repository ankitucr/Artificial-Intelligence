# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_66.py", line 56, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_66.py", line 51, in main
    print(web_reader.get_content())
          ~~~~~~~~~~~~~~~~~~~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_66.py", line 35, in get_content
    response = requests.get(self.url)
               ^^^^^^^^
NameError: name 'requests' is not defined. Did you mean: 'self.requests'?


import sqlite3
import json

class MicroSkill:
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def save_to_db(self):
        conn = sqlite3.connect('shared_memory.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS micro_skills (
                name text,
                description text
                )""")
        c.execute("INSERT INTO micro_skills VALUES (?,?)", (self.name, self.description))
        conn.commit()
        conn.close()

    @staticmethod
    def get_all_skills():
        conn = sqlite3.connect('shared_memory.db')
        c = conn.cursor()
        c.execute("SELECT * FROM micro_skills")
        skills = c.fetchall()
        conn.close()
        return skills

class WebReader:
    import requests
    def __init__(self, url):
        self.url = url

    def get_content(self):
        response = requests.get(self.url)
        return response.text

def create_skill():
    name = input("Enter skill name: ")
    description = input("Enter skill description: ")
    skill = MicroSkill(name, description)
    skill.save_to_db()
    return skill

def main():
    failed_attempts = 131
    if failed_attempts > 100:
        print("Suggesting new skill: web reader")
        url = "https://duckduckgo.com/"
        web_reader = WebReader(url)
        print(web_reader.get_content())
    skill = create_skill()
    print("Created skill:", skill.name)

if __name__ == "__main__":
    main()