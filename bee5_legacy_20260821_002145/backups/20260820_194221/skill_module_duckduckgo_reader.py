# duckduckgo_reader micro-skill
import requests
def execute_skill(query):
    url = 'https://api.duckduckgo.com/?q=' + query + '&format=json'
    response = requests.get(url)
    return response.json()
