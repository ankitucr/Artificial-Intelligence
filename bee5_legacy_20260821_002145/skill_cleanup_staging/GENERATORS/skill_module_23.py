import sqlite3
import requests
from bs4 import BeautifulSoup

def add_skill(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (name text, description text)''')
    c.execute("INSERT INTO skills VALUES (?,?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def get_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skills WHERE name=?", (skill_name,))
    skill = c.fetchone()
    conn.close()
    return skill

def web_search(query):
    url = f"https://duckduckgo.com/html?q={query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.get_text()

def main():
    new_skill_name = "web_search"
    new_skill_description = "Search the web using duckduckgo"
    add_skill(new_skill_name, new_skill_description)
    print(get_skill(new_skill_name))
    print(web_search("python programming"))

if __name__ == "__main__":
    main()