import requests
import os

url = 'http://127.0.0.1:5000/movies_api?page=1&per_page=20'
try:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    print('has_next:', data.get('has_next'))
    for i, m in enumerate(data.get('results', [])[:10], 1):
        print(i, m.get('title'), m.get('poster_url')[:200])
except Exception as e:
    print('Error fetching movies_api:', e)
