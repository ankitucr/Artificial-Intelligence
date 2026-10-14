# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_73.py", line 46, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_73.py", line 40, in main
    add_skill(new_skill)
    ~~~~~~~~~^^^^^^^^^^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_73.py", line 10, in add_skill
    c.execute("INSERT INTO skills VALUES (?)", (skill_name,))
    ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: table skills has 2 columns but 1 values were supplied


import sqlite3
import requests
from bs4 import BeautifulSoup

def add_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (skill_name text)''')
    c.execute("INSERT INTO skills VALUES (?)", (skill_name,))
    conn.commit()
    conn.close()

def get_active_skills():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skills")
    skills = [row[0] for row in c.fetchall()]
    conn.close()
    return skills

def print_current_status(active_skills, failed_attempts):
    print(f"Current Active Skills: {active_skills}")
    print(f"Failed Attempts in memory: {failed_attempts}")

def read_from_duckduckgo(query):
    url = f"https://duckduckgo.com/html/?q={query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    results = []
    for result in soup.find_all('a', class_='result__a'):
        results.append(result.text)
    return results

def main():
    active_skills = get_active_skills()
    failed_attempts = 143
    print_current_status(active_skills, failed_attempts)
    new_skill = "web_search"
    add_skill(new_skill)
    query = "python programming"
    results = read_from_duckduckgo(query)
    print(f"Results for '{query}': {results}")

if __name__ == "__main__":
    main()