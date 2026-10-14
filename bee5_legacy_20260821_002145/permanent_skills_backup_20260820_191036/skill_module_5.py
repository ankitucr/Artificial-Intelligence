import sqlite3
import requests
from bs4 import BeautifulSoup

def add_micro_skill(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS micro_skills
                 (name text, description text)''')
    c.execute("INSERT INTO micro_skills VALUES (?,?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def get_web_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.get_text()

def learn_from_duckduckgo(query):
    url = f"https://duckduckgo.com/html?q={query}"
    return get_web_content(url)

add_micro_skill('web_scraper', 'ability to scrape web content')
print(learn_from_duckduckgo('python+neural+networks'))