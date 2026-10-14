import sqlite3
import requests
from bs4 import BeautifulSoup

def get_skill_data(skill_name):
    url = f"https://duckduckgo.com/?q={skill_name}&t=h_&ia=web"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.get_text()

def add_skill(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (name text, description text)''')
    c.execute("INSERT INTO skills VALUES (?,?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def main():
    skill_name = "Web Scraping"
    skill_description = get_skill_data(skill_name)
    add_skill(skill_name, skill_description)
    print(f"Skill '{skill_name}' added successfully.")

if __name__ == "__main__":
    main()