# ERROR: Traceback (most recent call last):
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_55.py", line 40, in <module>
    main()
    ~~~~^^
  File "/data/data/com.termux/files/home/bee5/sandbox/skill_module_55.py", line 30, in main
    cursor.execute('SELECT text FROM data WHERE id = 1')
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sqlite3.OperationalError: no such column: text


import sqlite3
import requests

def check_internet_connection():
    try:
        requests.head('https://www.google.com', timeout=1)
        return True
    except requests.ConnectionError:
        return False

def text_summarization_micro_skill(text):
    if not check_internet_connection():
        return "No internet connection"

    api_url = 'https://api-inference.huggingface.co/models/t5-base'
    headers = {'Authorization': 'Bearer YOUR_HUGGINGFACE_TOKEN'}
    data = {'inputs': text}

    try:
        response = requests.post(api_url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()[0]['summary_text']
    except requests.RequestException as e:
        return str(e)

def main():
    conn = sqlite3.connect('shared_memory.db')
    cursor = conn.cursor()

    cursor.execute('SELECT text FROM data WHERE id = 1')
    text = cursor.fetchone()[0]

    summary = text_summarization_micro_skill(text)

    cursor.execute('UPDATE data SET summary =? WHERE id = 1', (summary,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()