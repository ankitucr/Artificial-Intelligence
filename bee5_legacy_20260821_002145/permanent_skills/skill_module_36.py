import sqlite3
import requests
from bs4 import BeautifulSoup

def get_new_skill():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (skill_name text, skill_code text)''')
    conn.commit()
    conn.close()

    url = "https://duckduckgo.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    new_skill_name = soup.find('a').text
    new_skill_code = f"skill_module_{hash(new_skill_name)}"

    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skills VALUES (?, ?)", (new_skill_name, new_skill_code))
    conn.commit()
    conn.close()

    with open(f"{new_skill_code}.py", "w") as f:
        f.write(f"def {new_skill_name}():\n    pass")

get_new_skill()