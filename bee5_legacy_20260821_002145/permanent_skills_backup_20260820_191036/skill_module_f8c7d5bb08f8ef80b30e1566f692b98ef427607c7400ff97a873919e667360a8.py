
import requests
from bs4 import BeautifulSoup

def read_from_duckduckgo(query):
    url = f"https://duckduckgo.com/html?q={query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.get_text()

if __name__ == "__main__":
    query = "python"
    print(read_from_duckduckgo(query))
