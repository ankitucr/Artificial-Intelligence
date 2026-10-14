import sqlite3
import requests
from bs4 import BeautifulSoup

def create_micro_skill(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS micro_skills
                 (name text, description text)''')
    c.execute("INSERT INTO micro_skills VALUES (?, ?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def get_duckduckgo_search_results(query):
    url = f"https://duckduckgo.com/html?q={query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    results = [a.text for a in soup.find_all('a', class_='result__a')]
    return results

def add_micro_skill():
    skill_name = "web_search"
    skill_description = "Search the web using DuckDuckGo"
    create_micro_skill(skill_name, skill_description)
    print("Micro-skill added successfully")

def test_micro_skill():
    query = "Python programming"
    results = get_duckduckgo_search_results(query)
    print("Search results:")
    for result in results:
        print(result)

add_micro_skill()
test_micro_skill()