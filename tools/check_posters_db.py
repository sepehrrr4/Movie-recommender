import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parents[1] / 'instance' / 'movies.db'
conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM movie;")
total = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM movie WHERE poster_url IS NULL OR poster_url=''")
null_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM movie WHERE poster_url LIKE '%None%'")
none_count = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM movie WHERE poster_url LIKE '%placeholder%'")
placeholder_count = cur.fetchone()[0]

print(f"Total: {total}\nposter NULL/empty: {null_count}\nposter contains 'None': {none_count}\nposter placeholder: {placeholder_count}")

cur.execute("SELECT id, title, poster_url FROM movie WHERE poster_url LIKE '%None%' LIMIT 10")
rows = cur.fetchall()
if rows:
    print('\nSamples with None in poster_url:')
    for r in rows:
        print(r)

conn.close()
