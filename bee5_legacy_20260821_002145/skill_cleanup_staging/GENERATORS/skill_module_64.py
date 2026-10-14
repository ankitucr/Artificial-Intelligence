import sqlite3
import requests
from bs4 import BeautifulSoup

def add_skill(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS skills (name TEXT, description TEXT)')
    c.execute('INSERT INTO skills VALUES (?,?)', (skill_name, skill_description))
    conn.commit()
    conn.close()

def web_scraper(skill_name):
    url = f'https://duckduckgo.com/html?q={skill_name}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup.prettify()

def evaluate_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('SELECT * FROM skills WHERE name=?', (skill_name,))
    skill = c.fetchone()
    conn.close()
    if skill:
        return skill[1]
    else:
        return "Skill not found"

def new_skill():
    new_skill_name = 'web_search'
    new_skill_description = 'Scrapes duckduckgo for information'
    add_skill(new_skill_name, new_skill_description)
    print(f"Added new skill: {new_skill_name}")

new_skill()