import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')
from app import app

queries = ["Inception", "The", "Matrix", "Avatar", "NonExistingTitleXYZ"]

with app.test_client() as c:
    for q in queries:
        resp = c.get(f'/search?q={q}')
        print(f'Query: {q} status={resp.status_code}')
        if resp.status_code == 200:
            data = resp.get_json()
            print(f'  Results: {len(data)}')
            for m in data[:3]:
                print('   -', m.get('title'), '| src:', m.get('source'), '| poster:', ('ok' if m.get('poster_url') else 'none'))
        else:
            print('  Error response body:', resp.data[:200])
