import sqlite3
import requests
from bs4 import BeautifulSoup

def add_micro_skill(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS micro_skills
                 (name text, description text)''')
    c.execute("INSERT INTO micro_skills VALUES (?, ?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def get_micro_skills():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM micro_skills")
    skills = c.fetchall()
    conn.close()
    return skills

def duckduckgo_search(query):
    url = "https://duckduckgo.com/html"
    params = {"q": query}
    response = requests.post(url, data=params)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.get_text()

def main():
    new_skill = "web_search"
    add_micro_skill(new_skill, "Perform a web search using DuckDuckGo")
    skills = get_micro_skills()
    for skill in skills:
        print(skill)
    query = "python programming"
    print(duckduckgo_search(query))

if __name__ == "__main__":
    main()