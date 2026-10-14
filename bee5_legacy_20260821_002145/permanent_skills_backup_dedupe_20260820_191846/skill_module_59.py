import sqlite3
import importlib.util

def create_neural_network_node(input_dim, output_dim):
    spec = importlib.util.find_spec("numpy")
    if spec is None:
        print("numpy is not installed")
        return None

    import numpy as np
    node = {
        "weights": np.random.rand(input_dim, output_dim),
        "bias": np.zeros((1, output_dim))
    }
    return node

def save_to_db(data):
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS neural_network (
                data text
                )""")
    c.execute("INSERT INTO neural_network VALUES (?)", (str(data),))
    conn.commit()
    conn.close()

def main():
    node = create_neural_network_node(10, 10)
    if node is not None:
        save_to_db(node)

main()