import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')

from app import app
import json

with app.test_client() as c:
    resp = c.get('/movies_api?page=1&per_page=20')
    print('status', resp.status_code)
    try:
        data = resp.get_json()
        print('has_next:', data.get('has_next'))
        results = data.get('results', [])
        print('results_len:', len(results))
        print(json.dumps(results[:10], indent=2, ensure_ascii=False))
    except Exception as e:
        print('error parsing json', e)
