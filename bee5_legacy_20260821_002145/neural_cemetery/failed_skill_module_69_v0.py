# ERROR: Timeout Error: Code Execution took longer than 10 seconds.

import sqlite3
import requests
from bs4 import BeautifulSoup

def fetch_definition(term):
    url = f"https://api.duckduckgo.com/?q={term}&format=json"
    response = requests.get(url)
    data = response.json()
    definition = data.get("Abstract", "No definition found")
    return definition

def save_skill(skill_name, skill_definition):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS skills
                 (name text, definition text)""")
    c.execute("INSERT INTO skills VALUES (?, ?)", (skill_name, skill_definition))
    conn.commit()
    conn.close()

def add_skill():
    skill_name = input("Enter the name of the new skill: ")
    definition = fetch_definition(skill_name)
    save_skill(skill_name, definition)
    print(f"Skill '{skill_name}' added with definition: {definition}")

add_skill()