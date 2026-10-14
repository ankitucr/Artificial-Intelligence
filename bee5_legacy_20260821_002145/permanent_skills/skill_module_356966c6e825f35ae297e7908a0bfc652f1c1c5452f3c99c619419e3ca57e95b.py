
import requests

def read_from_duckduckgo(query):
    response = requests.get(f"https://api.duckduckgo.com/?q={query}&format=json")
    return response.json()
