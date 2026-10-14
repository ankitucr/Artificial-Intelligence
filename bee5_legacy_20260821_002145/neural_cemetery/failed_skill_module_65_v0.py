# ERROR: Timeout Error: Code Execution took longer than 10 seconds.

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

def fetch_skill_idea():
    url = "https://duckduckgo.com/html?q=python+micro+skills"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    skill_ideas = [a.text for a in soup.find_all('a', class_='result__a')]
    return skill_ideas

def select_skill_idea(skill_ideas):
    for i, idea in enumerate(skill_ideas):
        print(f"{i+1}. {idea}")
    choice = int(input("Select a skill idea: ")) - 1
    return skill_ideas[choice]

def main():
    skill_ideas = fetch_skill_idea()
    selected_skill = select_skill_idea(skill_ideas)
    add_micro_skill(selected_skill, "New micro-skill added")
    print(f"Micro-skill '{selected_skill}' added successfully")

if __name__ == "__main__":
    main()