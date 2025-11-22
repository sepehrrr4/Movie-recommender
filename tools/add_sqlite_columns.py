import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / 'instance' / 'movies.db'

def ensure_columns():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(movie);")
    cols = [r[1] for r in cur.fetchall()]

    if 'tmdb_id' not in cols:
        print('Adding column tmdb_id...')
        cur.execute('ALTER TABLE movie ADD COLUMN tmdb_id INTEGER;')
    else:
        print('Column tmdb_id already exists.')

    if 'imdb_id' not in cols:
        print('Adding column imdb_id...')
        cur.execute('ALTER TABLE movie ADD COLUMN imdb_id TEXT;')
    else:
        print('Column imdb_id already exists.')

    if 'vote_average' not in cols:
        print('Adding column vote_average...')
        cur.execute('ALTER TABLE movie ADD COLUMN vote_average REAL;')
    else:
        print('Column vote_average already exists.')

    if 'vote_count' not in cols:
        print('Adding column vote_count...')
        cur.execute('ALTER TABLE movie ADD COLUMN vote_count INTEGER;')
    else:
        print('Column vote_count already exists.')

    conn.commit()
    conn.close()

if __name__ == '__main__':
    if not DB_PATH.exists():
        print(f'Database not found at {DB_PATH}. Run seed.py first.')
    else:
        ensure_columns()
