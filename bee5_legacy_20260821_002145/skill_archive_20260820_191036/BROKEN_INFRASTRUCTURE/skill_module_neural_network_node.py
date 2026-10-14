# skill_module_neural_network_node.py
import sqlite3

def neural_network_node():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("SELECT * FROM skill_modules WHERE name=?", ('neural_network_node',))
    row = c.fetchone()
    conn.close()
    return row

neural_network_node()
