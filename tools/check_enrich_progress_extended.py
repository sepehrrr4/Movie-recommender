import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')
from app import app
from models import db, Movie

with app.app_context():
    total = Movie.query.count()
    posters = Movie.query.filter(Movie.poster_url.isnot(None)).filter(~Movie.poster_url.like('%No+Image%')).count()
    tmdb_ids = Movie.query.filter(Movie.tmdb_id.isnot(None)).count()
    votes = Movie.query.filter(Movie.vote_average.isnot(None)).count()
    print(f'Total movies: {total}')
    print(f'With tmdb_id: {tmdb_ids}')
    print(f'With poster_url (real): {posters}')
    print(f'With vote_average: {votes}')
    remaining = total - posters
    print(f'Remaining needing posters: {remaining}')
