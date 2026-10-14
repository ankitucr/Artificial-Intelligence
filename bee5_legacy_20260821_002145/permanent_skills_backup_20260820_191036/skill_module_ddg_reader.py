
import requests
from bs4 import BeautifulSoup

def get_ddg_answer(query):
    url = f"https://duckduckgo.com/html?q={query}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    answer = soup.find('a', class_='result__a')
    return answer.text
