from pathlib import Path
import sqlite3

DB = Path(__file__).resolve().parents[1] / 'instance' / 'movies.db'
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM movie WHERE tmdb_id IS NOT NULL;")
with_tmdb = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM movie WHERE poster_url IS NOT NULL AND poster_url NOT LIKE '%No+Image%';")
with_poster = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM movie;")
total = cur.fetchone()[0]
print(f"Total movies: {total}\nWith tmdb_id: {with_tmdb}\nWith poster_url (not placeholder): {with_poster}")
conn.close()
