import sqlite3
import requests
from bs4 import BeautifulSoup

def retrieve_ddg_data(search_query):
    url = f"https://duckduckgo.com/html?q={search_query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.get_text()

def save_data(data, table_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (data TEXT)")
    c.execute(f"INSERT INTO {table_name} VALUES (?)", (data,))
    conn.commit()
    conn.close()

def load_data(table_name):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute(f"SELECT data FROM {table_name}")
    data = c.fetchone()
    conn.close()
    return data

def add_micro_skill(search_query, table_name):
    data = retrieve_ddg_data(search_query)
    save_data(data, table_name)

add_micro_skill("python neural network", "new_skill")