import sqlite3
import webbrowser
import requests
from bs4 import BeautifulSoup

def duckduckgo_search(query):
    url = 'https://duckduckgo.com/html'
    params = {'q': query}
    response = requests.post(url, data=params)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.find('a', class_='result__a')

def add_micro_skill(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS micro_skills (name TEXT, description TEXT)')
    c.execute('INSERT INTO micro_skills VALUES (?,?)', (skill_name, skill_description))
    conn.commit()
    conn.close()

def get_micro_skills():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('SELECT * FROM micro_skills')
    skills = c.fetchall()
    conn.close()
    return skills

def main():
    add_micro_skill('web_search', 'Perform a search on duckduckgo')
    skill = get_micro_skills()[0]
    query = 'test search query'
    result = duckduckgo_search(query)
    if result:
        print(f'Found result: {result.get("href")}')
    else:
        print('No result found')

if __name__ == '__main__':
    main()