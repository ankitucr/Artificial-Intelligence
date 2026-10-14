import requests
def search(query):
    url = 'https://api.duckduckgo.com/'
    params = {'q': query, 'format': 'json'}
    response = requests.get(url, params=params)
    return response.json()