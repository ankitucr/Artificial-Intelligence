# Module 345
def get_info(query):
    url = 'https://duckduckgo.com/html/'
    params = {'q': query}
    response = requests.get(url, params=params)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.find('a', class_='result__a').text
