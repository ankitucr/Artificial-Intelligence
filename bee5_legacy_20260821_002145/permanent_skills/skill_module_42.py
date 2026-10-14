import sqlite3
import requests

def create_skill_module():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS skill_modules
                 (name text, description text)''')
    conn.commit()
    conn.close()

def add_skill_module(name, description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("INSERT INTO skill_modules VALUES (?, ?)", (name, description))
    conn.commit()
    conn.close()

def get_skill_modules():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skill_modules")
    rows = c.fetchall()
    conn.close()
    return rows

def duckduckgo_search(query):
    url = f"https://api.duckduckgo.com/?q={query}&format=json"
    response = requests.get(url)
    return response.json()

def create_neural_network_node():
    # TO DO: implement neural network node creation
    pass

def main():
    create_skill_module()
    add_skill_module('skill_module_web_scraper', 'A micro-skill for web scraping using duckduckgo API')
    print(get_skill_modules())
    query = "python neural networks"
    print(duckduckgo_search(query))

if __name__ == "__main__":
    main()