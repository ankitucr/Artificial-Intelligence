import sqlite3
import requests

def add_skill(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (name text, description text)''')
    c.execute("INSERT INTO skills VALUES (?, ?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def get_skills():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skills")
    skills = c.fetchall()
    conn.close()
    return skills

def web_search(query):
    url = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json"}
    response = requests.get(url, params=params)
    return response.json()

def add_web_search_skill():
    add_skill('web_search', 'Search the web using DuckDuckGo API')

def main():
    add_web_search_skill()
    skills = get_skills()
    print(skills)

if __name__ == "__main__":
    main()