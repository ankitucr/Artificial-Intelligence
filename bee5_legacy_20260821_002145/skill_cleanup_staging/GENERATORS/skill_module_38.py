import sqlite3
import requests

def create_skill(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skills
                 (name text, description text)''')
    c.execute("INSERT INTO skills VALUES (?, ?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def add_web_search_skill():
    create_skill('web_search', 'Searches DuckDuckGo for a given query')
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS web_search_history
                 (query text, result text)''')
    conn.commit()
    conn.close()

def search_duckduckgo(query):
    url = 'https://api.duckduckgo.com/'
    params = {'q': query, 'format': 'json'}
    response = requests.get(url, params=params)
    return response.json()

def save_search_result(query, result):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO web_search_history VALUES (?, ?)", (query, str(result)))
    conn.commit()
    conn.close()

add_web_search_skill()
print(search_duckduckgo('python programming'))
save_search_result('python programming', search_duckduckgo('python programming'))