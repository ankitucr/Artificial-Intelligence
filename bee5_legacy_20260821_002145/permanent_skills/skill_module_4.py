import sqlite3
conn = sqlite3.connect('shared_memory.db', timeout=30)
cur = conn.cursor()
cur.execute('PRAGMA busy_timeout=30000')
conn.commit()
conn.close()