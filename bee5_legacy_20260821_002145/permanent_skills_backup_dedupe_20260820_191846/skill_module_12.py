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

def add_duckduckgo_reader():
    skill_name = "duckduckgo_reader"
    skill_description = "Reads information from DuckDuckGo"
    create_micro_skill(skill_name, skill_description)

    def read_from_duckduckgo(query):
        url = f"https://duckduckgo.com/html?q={query}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.get_text()

    with open(f"skill_module_{len([name for name in globals() if name.startswith('skill_module_')]) + 1}.py", "w") as f:
        f.write(f"def read_from_duckduckgo(query):\n")
        f.write(f"    url = f\"https://duckduckgo.com/html?q={{query}}\"\n")
        f.write(f"    response = requests.get(url)\n")
        f.write(f"    soup = BeautifulSoup(response.text, 'html.parser')\n")
        f.write(f"    return soup.get_text()\n")

add_duckduckgo_reader()