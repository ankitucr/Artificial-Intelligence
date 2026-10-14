# ERROR: Timeout Error: Code Execution took longer than 10 seconds.

import sqlite3
import requests

class WebReader:
    def __init__(self, url):
        self.url = url

    def get_content(self):
        try:
            response = requests.get(self.url)
            return response.text
        except requests.exceptions.RequestException as e:
            return f"An error occurred: {e}"

def main():
    conn = sqlite3.connect('shared_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS urls
                 (url text)''')
    conn.commit()
    conn.close()

    url = "http://example.com"
    web_reader = WebReader(url)
    print(web_reader.get_content())

if __name__ == "__main__":
    main()