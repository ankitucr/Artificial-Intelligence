import sqlite3
import os

def create_new_skill():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (skill_name text, skill_content text)''')
    conn.commit()
    conn.close()

def generate_skill_module(skill_name, skill_content):
    module_name = f"skill_module_{hash(skill_name)}"
    with open(f"{module_name}.py", "w") as f:
        f.write(skill_content)
    return module_name

def add_skill_to_database(skill_name, skill_content):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills VALUES (?,?)", (skill_name, skill_content))
    conn.commit()
    conn.close()

def get_new_skill_name():
    return "micro_skill_duckduckgo_reader"

def get_new_skill_content():
    return """
import requests
from bs4 import BeautifulSoup

def read_from_duckduckgo(query):
    url = f"https://duckduckgo.com/html/?q={query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup.get_text()

print(read_from_duckduckgo("example query"))
"""

create_new_skill()
skill_name = get_new_skill_name()
skill_content = get_new_skill_content()
module_name = generate_skill_module(skill_name, skill_content)
add_skill_to_database(skill_name, skill_content)
print(f"Added new skill module: {module_name}.py")