import sqlite3
import random

class MicroSkill:
    def __init__(self, name, skill_type):
        self.name = name
        self.skill_type = skill_type

    def save(self):
        conn = sqlite3.connect('shared_memory.db')
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS micro_skills
                     (name text, skill_type text)""")
        c.execute("INSERT INTO micro_skills VALUES (?,?)",
                  (self.name, self.skill_type))
        conn.commit()
        conn.close()

    def get_skills(self):
        conn = sqlite3.connect('shared_memory.db')
        c = conn.cursor()
        c.execute("SELECT * FROM micro_skills")
        skills = c.fetchall()
        conn.close()
        return skills

class WebSearchSkill(MicroSkill):
    def __init__(self):
        super().__init__('web_search', 'information_retrieval')

    def search(self, query):
        import requests
        url = 'https://api.duckduckgo.com/'
        params = {'q': query, 'format': 'json'}
        response = requests.get(url, params=params)
        return response.json()

def main():
    web_search_skill = WebSearchSkill()
    web_search_skill.save()
    skills = MicroSkill('micro_skill', 'micro_skill').get_skills()
    print(skills)

if __name__ == '__main__':
    main()