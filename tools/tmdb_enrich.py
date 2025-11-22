import os
import time
import json
import argparse
import requests
from urllib.parse import quote_plus
from dotenv import load_dotenv
import sys
from pathlib import Path

# ensure project root is on sys.path so `from app import app` works when running from tools/
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app
from models import db, Movie

# load .env from project root if present
load_dotenv(dotenv_path=ROOT / '.env')

CACHE_PATH = os.path.join('tools', '.tmdb_cache.json')
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p/w500'


def load_cache():
    try:
        with open(CACHE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_cache(cache):
    with open(CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def tmdb_search(api_key, title, year=None):
    q = title.strip()
    query_key = f"search::{q}::{year or ''}"
    cache = load_cache()
    if query_key in cache:
        return cache[query_key]

    url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={quote_plus(q)}"
    if year:
        url += f"&year={year}"

    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        return None
    data = r.json()
    result = data.get('results', [])
    cache[query_key] = result
    save_cache(cache)
    time.sleep(0.25)
    return result


def tmdb_get_movie(api_key, tmdb_id):
    cache = load_cache()
    key = f"movie::{tmdb_id}"
    if key in cache:
        return cache[key]
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}&append_to_response=credits"
    r = requests.get(url, timeout=15)
    if r.status_code != 200:
        return None
    data = r.json()
    cache[key] = data
    save_cache(cache)
    time.sleep(0.2)
    return data


def update_movie_from_tmdb(movie, tmdb_data):
    # poster
    poster_path = tmdb_data.get('poster_path')
    if poster_path:
        movie.poster_url = TMDB_IMAGE_BASE + poster_path

    # basic vote stats
    vote_avg = tmdb_data.get('vote_average')
    vote_cnt = tmdb_data.get('vote_count')
    if vote_avg is not None:
        movie.vote_average = vote_avg
    if vote_cnt is not None:
        movie.vote_count = vote_cnt

    # credits -> director, actors, writers
    credits = tmdb_data.get('credits', {})
    crew = credits.get('crew', [])
    cast = credits.get('cast', [])

    # director
    director = next((c.get('name') for c in crew if c.get('job') == 'Director'), None)
    if director:
        movie.director = director

    # top 3 actors
    top_actors = [c.get('name') for c in cast[:3] if c.get('name')]
    if top_actors:
        movie.actors = ', '.join(top_actors)

    # writers
    writers = [c.get('name') for c in crew if c.get('job') and 'write' in c.get('job').lower()]
    if writers:
        movie.writer = ', '.join(writers)


def run_enrichment(api_key, limit=None, only_missing_poster=True, batch_commit=25, sleep_between=0.15):
    with app.app_context():
        q = Movie.query
        if only_missing_poster:
            q = q.filter((Movie.poster_url == None) | (Movie.poster_url.like('%No+Image%')))
        movies = q.order_by(Movie.id).all()
        total = len(movies)
        print(f"Found {total} movies to process (limit={limit})")

        processed = 0
        for movie in movies:
            if limit and processed >= limit:
                break

            title = movie.title
            year = movie.year

            results = tmdb_search(api_key, title, year)
            if not results:
                processed += 1
                continue

            # prefer exact year+title match when possible
            selected = None
            for r in results:
                if r.get('title', '').strip().lower() == title.strip().lower():
                    if year and r.get('release_date', '').startswith(str(year)):
                        selected = r
                        break
            if not selected:
                selected = results[0]

            tmdb_id = selected.get('id')
            movie.tmdb_id = tmdb_id

            tmdb_data = tmdb_get_movie(api_key, tmdb_id)
            if tmdb_data:
                update_movie_from_tmdb(movie, tmdb_data)

            db.session.add(movie)

            # commit every batch_commit
            if processed % batch_commit == 0:
                db.session.commit()
                print(f"Committed batch at processed={processed}")

            # polite rate limiting
            time.sleep(sleep_between)

            processed += 1

        db.session.commit()
        print(f"Enrichment complete. Processed {processed} movies.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, default=None, help='Limit number of movies to process')
    parser.add_argument('--all', action='store_true', help='Process all movies, not only those missing posters')
    args = parser.parse_args()

    api_key = os.environ.get('TMDB_API_KEY')
    if not api_key:
        print('TMDB_API_KEY not found in environment. Set TMDB_API_KEY and retry.')
        return

    run_enrichment(api_key, limit=args.limit, only_missing_poster=not args.all)


if __name__ == '__main__':
    main()
