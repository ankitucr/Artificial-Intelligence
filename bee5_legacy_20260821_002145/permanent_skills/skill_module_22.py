import sqlite3
import requests

def add_micro_skill(skill_name, skill_description):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS micro_skills
                 (name text, description text)''')
    c.execute("INSERT INTO micro_skills VALUES (?,?)", (skill_name, skill_description))
    conn.commit()
    conn.close()

def get_macro_skill(skill_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT description FROM micro_skills WHERE name=?", (skill_name,))
    result = c.fetchone()
    conn.close()
    return result

def fetch_duckduckgo(query):
    response = requests.get(f"https://api.duckduckgo.com/?q={query}&format=json")
    return response.json()

def main():
    skill_name = "web_search"
    skill_description = "Fetches information from duckduckgo."
    add_micro_skill(skill_name, skill_description)

if __name__ == "__main__":
    main()