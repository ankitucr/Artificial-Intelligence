
import requests
from bs4 import BeautifulSoup

def duckduckgo_learning(query):
    url = "https://duckduckgo.com/html/"
    params = {"q": query}
    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.text, "html.parser")
    return soup.find("a", class_="result__a").text
        