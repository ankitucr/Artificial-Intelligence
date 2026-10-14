
import sqlite3

def duckduckgo_search():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skill_modules WHERE name=?", (duckduckgo_search,))
    result = c.fetchone()
    conn.close()
    return result

duckduckgo_search()
