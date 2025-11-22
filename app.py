from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from models import db, Movie
import requests
from urllib.parse import quote_plus
from collections import defaultdict
import os
import uuid
from dotenv import load_dotenv

# Load environment variables (.env) early so TMDB_API_KEY is available when app starts
load_dotenv()

# Simple in-memory store for recommendations keyed by a short token.
# This avoids putting large lists into the cookie-based session.
RECS_STORE = {}

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)
db.init_app(app)

# TMDb settings
TMDB_API_KEY = os.environ.get('TMDB_API_KEY')
TMDB_IMAGE_BASE = 'https://image.tmdb.org/t/p'

# simple in-memory cache for discovered top movies
TMDB_DISCOVER_CACHE = {'ts': 0, 'movies': []}
TMDB_CACHE_TTL = 60 * 60  # 1 hour


def tmdb_popular(page=1):
    if not TMDB_API_KEY:
        return []
    url = f'https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&page={page}'
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return []
    data = r.json()
    results = []
    for item in data.get('results', []):
        poster = item.get('poster_path')
        poster_url = (TMDB_IMAGE_BASE + '/w342' + poster) if poster else 'https://via.placeholder.com/500x750.png?text=No+Image'
        results.append({
            'db_id': None,
            'tmdb_id': item.get('id'),
            'title': item.get('title'),
            'poster_url': poster_url,
            'description': item.get('overview')
        })
    return results


def tmdb_movie_detail(tmdb_id):
    if not TMDB_API_KEY:
        return None
    url = f'https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=credits,videos'
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return None
    data = r.json()
    poster = data.get('poster_path')
    poster_url = (TMDB_IMAGE_BASE + '/w500' + poster) if poster else 'https://via.placeholder.com/500x750.png?text=No+Image'
    
    # extract director, top actors with photos
    director = None
    actors_list = []
    crew = data.get('credits', {}).get('crew', [])
    cast = data.get('credits', {}).get('cast', [])
    for c in crew:
        if c.get('job') == 'Director':
            director = c.get('name')
            break
    
    for c in cast[:10]:
        if c.get('name'):
            profile_path = c.get('profile_path')
            profile_url = (TMDB_IMAGE_BASE + '/w185' + profile_path) if profile_path else 'https://via.placeholder.com/185x278.png?text=No+Photo'
            actors_list.append({
                'name': c.get('name'),
                'character': c.get('character', ''),
                'profile_url': profile_url
            })
    
    # extract trailer (look for YouTube trailer)
    trailer_key = None
    videos = data.get('videos', {}).get('results', [])
    for video in videos:
        if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
            trailer_key = video.get('key')
            break
    
    return {
        'tmdb_id': data.get('id'),
        'title': data.get('title'),
        'poster_url': poster_url,
        'description': data.get('overview'),
        'director': director,
        'actors': ', '.join([a['name'] for a in actors_list]),
        'actors_list': actors_list,
        'genre': ', '.join([g.get('name') for g in data.get('genres', [])]),
        'year': (data.get('release_date') or '')[:4] if data.get('release_date') else None,
        'vote_average': data.get('vote_average'),
        'vote_count': data.get('vote_count'),
        'trailer_key': trailer_key
    }


def get_top_tmdb_movies(page=1, per_page=20, min_vote_count=50, sort_by='rating', order='desc', min_rating=0.0):
    """Fetch movies from TMDb discover API with pagination support for infinite scroll."""
    sort_mapping = {
        'rating': 'vote_average',
        'year': 'primary_release_date',
        'title': 'original_title'
    }
    tmdb_sort_field = sort_mapping.get(sort_by, 'vote_average')
    tmdb_order = 'asc' if order == 'asc' else 'desc'
    sort_param = f'{tmdb_sort_field}.{tmdb_order}'

    min_rating = max(0.0, min(10.0, float(min_rating or 0.0)))

    url = (
        f'https://api.themoviedb.org/3/discover/movie'
        f'?api_key={TMDB_API_KEY}'
        f'&sort_by={sort_param}'
        f'&vote_count.gte={min_vote_count}'
        f'&page={page}'
        f'&include_adult=false'
    )

    if min_rating > 0:
        url += f'&vote_average.gte={min_rating}'
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return {'results': [], 'total_pages': 0, 'page': page}
        
        data = r.json()
        movies = []
        for item in data.get('results', [])[:per_page]:
            poster = item.get('poster_path')
            poster_url = (TMDB_IMAGE_BASE + '/w342' + poster) if poster else 'https://via.placeholder.com/500x750.png?text=No+Image'
            movies.append({
                'tmdb_id': item.get('id'),
                'title': item.get('title'),
                'poster_url': poster_url,
                'overview': item.get('overview') or '',
                'year': (item.get('release_date') or '')[:4],
                'vote_average': item.get('vote_average') or 0,
                'vote_count': item.get('vote_count') or 0
            })
        
        return {
            'results': movies,
            'total_pages': data.get('total_pages', 1),
            'page': page
        }
    except Exception as e:
        print(f"TMDb API error: {e}")
        return {'results': [], 'total_pages': 0, 'page': page}

def get_tmdb_trending_week():
    """Fetch trending movies this week from TMDb."""
    if not TMDB_API_KEY:
        return []
    try:
        url = f'https://api.themoviedb.org/3/trending/movie/week?api_key={TMDB_API_KEY}'
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
        movies = []
        for item in data.get('results', [])[:10]:
            poster = item.get('poster_path')
            poster_url = (TMDB_IMAGE_BASE + '/w342' + poster) if poster else 'https://via.placeholder.com/500x750.png?text=No+Image'
            movies.append({
                'tmdb_id': item.get('id'),
                'title': item.get('title'),
                'poster_url': poster_url,
                'overview': item.get('overview') or '',
                'year': (item.get('release_date') or '')[:4],
                'vote_average': item.get('vote_average') or 0
            })
        return movies
    except Exception as e:
        print(f"TMDb trending API error: {e}")
        return []


def get_tmdb_now_playing():
    """Fetch now playing movies in theaters from TMDb."""
    if not TMDB_API_KEY:
        return []
    try:
        url = f'https://api.themoviedb.org/3/movie/now_playing?api_key={TMDB_API_KEY}&region=US'
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
        movies = []
        for item in data.get('results', [])[:10]:
            poster = item.get('poster_path')
            poster_url = (TMDB_IMAGE_BASE + '/w342' + poster) if poster else 'https://via.placeholder.com/500x750.png?text=No+Image'
            movies.append({
                'tmdb_id': item.get('id'),
                'title': item.get('title'),
                'poster_url': poster_url,
                'overview': item.get('overview') or '',
                'year': (item.get('release_date') or '')[:4],
                'vote_average': item.get('vote_average') or 0
            })
        return movies
    except Exception as e:
        print(f"TMDb now playing API error: {e}")
        return []


def get_tmdb_upcoming():
    """Fetch upcoming movies from TMDb."""
    if not TMDB_API_KEY:
        return []
    try:
        url = f'https://api.themoviedb.org/3/movie/upcoming?api_key={TMDB_API_KEY}&region=US'
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return []
        data = r.json()
        movies = []
        for item in data.get('results', [])[:10]:
            poster = item.get('poster_path')
            poster_url = (TMDB_IMAGE_BASE + '/w342' + poster) if poster else 'https://via.placeholder.com/500x750.png?text=No+Image'
            movies.append({
                'tmdb_id': item.get('id'),
                'title': item.get('title'),
                'poster_url': poster_url,
                'overview': item.get('overview') or '',
                'year': (item.get('release_date') or '')[:4],
                'vote_average': item.get('vote_average') or 0,
                'release_date': item.get('release_date') or ''
            })
        return movies
    except Exception as e:
        print(f"TMDb upcoming API error: {e}")
        return []


@app.route('/')
def home():
    """Renders the home page with movies loaded directly from TMDb API."""
    movies = []
    total_movies = 0
    trending = []
    now_playing = []
    upcoming = []
    has_next_initial = False
    
    if TMDB_API_KEY:
        try:
            data = get_top_tmdb_movies(page=1, per_page=20)
            movies = data.get('results', [])
            total_movies = data.get('total_pages', 0) * 20
            has_next_initial = data.get('total_pages', 0) > 1
            
            trending = get_tmdb_trending_week()
            now_playing = get_tmdb_now_playing()
            upcoming = get_tmdb_upcoming()
        except Exception as e:
            print(f"TMDb API error: {e}")
            movies = []
    
    return render_template('index.html', 
                         movies=movies, 
                         total_movies=total_movies,
                         has_next_initial=has_next_initial,
                         trending=trending,
                         now_playing=now_playing,
                         upcoming=upcoming)

@app.route('/search')
def search():
    """Searches for movies based on a query string and returns JSON."""
    query = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    if not query:
        return jsonify({'results': [], 'page': page, 'has_next': False})

    results = []
    # first, DB search (only on page 1)
    if page == 1:
        try:
            db_results = Movie.query.filter(Movie.title.ilike(f'%{query}%')).limit(10).all()
            for m in db_results:
                results.append({
                    'source': 'db',
                    'id': m.id,
                    'title': m.title,
                    'poster_url': m.poster_url,
                    'overview': m.description or '',
                    'year': m.year
                })
        except Exception:
            pass

    # then, TMDb search for richer results (de-duplicate by title)
    has_next = False
    if TMDB_API_KEY and len(query) >= 2:
        try:
            url = f'https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={quote_plus(query)}&page={page}'
            r = requests.get(url, timeout=8)
            if r.status_code == 200:
                data = r.json()
                has_next = data.get('page', 1) < data.get('total_pages', 1)
                seen_titles = {r['title'].lower() for r in results if 'title' in r}
                for item in data.get('results', [])[:20]:
                    title = item.get('title') or ''
                    if title.strip().lower() in seen_titles:
                        continue
                    poster = item.get('poster_path')
                    poster_url = (TMDB_IMAGE_BASE + '/w185' + poster) if poster else 'https://via.placeholder.com/200x300.png?text=No+Image'
                    results.append({
                        'source': 'tmdb',
                        'tmdb_id': item.get('id'),
                        'title': title,
                        'poster_url': poster_url,
                        'overview': item.get('overview') or '',
                        'year': (item.get('release_date') or '')[:4]
                    })
        except Exception:
            pass

    if page == 1:
        return jsonify(results)
    else:
        return jsonify({'results': results, 'page': page, 'has_next': has_next})


@app.route('/movies_api')
def movies_api():
    """Return paginated movies from TMDb API for infinite scroll. Params: page (1-based), per_page"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort_by', 'rating')
    order = request.args.get('order', 'desc')
    min_rating = request.args.get('min_rating', 0, type=float)
    if not TMDB_API_KEY:
        return jsonify({'results': [], 'page': page, 'has_next': False})

    data = get_top_tmdb_movies(
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        order=order,
        min_rating=min_rating
    )
    has_next = page < data.get('total_pages', 0)
    return jsonify({'results': data.get('results', []), 'page': page, 'has_next': has_next})

@app.route('/recommend', methods=['POST'])
def recommend():
    """Calculates and stores recommendations in the session, then redirects."""
    selected_movie_ids = request.form.getlist('movies')
    if not selected_movie_ids or len(selected_movie_ids) > 3:
        return "Please select up to three movies.", 400

    selected_movies = Movie.query.filter(Movie.id.in_(selected_movie_ids)).all()

    # Recommendation scoring: configurable weights
    WEIGHT_GENRE = 40
    WEIGHT_DIRECTOR = 20
    WEIGHT_WRITER = 10
    WEIGHT_ACTORS = 20
    WEIGHT_YEAR = 10
    ACTORS_TOP_N = 3
    YEAR_WINDOW = 5

    # build helper sets from selected movies
    union_selected_genres = set()
    union_selected_top_actors = set()
    selected_years = []
    selected_directors = set()
    selected_writers = set()
    for sm in selected_movies:
        if sm.genre:
            union_selected_genres.update([g.strip() for g in sm.genre.split(',') if g.strip()])
        if sm.actors:
            union_selected_top_actors.update([a.strip() for a in sm.actors.split(',')][:ACTORS_TOP_N])
        if getattr(sm, 'year', None):
            try:
                selected_years.append(int(sm.year))
            except Exception:
                pass
        if sm.director:
            selected_directors.add(sm.director.strip())
        if getattr(sm, 'writer', None):
            selected_writers.update([w.strip() for w in sm.writer.split(',') if w.strip()])

    mean_selected_year = None
    if selected_years:
        mean_selected_year = sum(selected_years) / len(selected_years)

    recommendations = defaultdict(float)
    for movie in Movie.query.filter(Movie.id.notin_(selected_movie_ids)).all():
        score = 0.0

        # candidate genres and actors
        movie_genres = set([g.strip() for g in (movie.genre or '').split(',') if g.strip()])
        movie_actors = [a.strip() for a in (movie.actors or '').split(',') if a.strip()]
        movie_top_actors = set(movie_actors[:ACTORS_TOP_N])

        # Genre score: proportion of union_selected_genres that candidate covers
        if union_selected_genres:
            shared_genres = union_selected_genres.intersection(movie_genres)
            # If user selections all share a single genre, require candidate to have it
            if len(union_selected_genres) == 1:
                only_genre = next(iter(union_selected_genres))
                if only_genre not in movie_genres:
                    # candidate doesn't have the required genre -> skip (score remains 0)
                    recommendations[movie.id] = 0.0
                    continue
            genre_fraction = len(shared_genres) / len(union_selected_genres)
            score += WEIGHT_GENRE * genre_fraction

        # Director / Writer score: split weights so each can contribute
        director_match = movie.director and movie.director.strip() in selected_directors
        writer_match = getattr(movie, 'writer', None) and any(w.strip() in selected_writers for w in (movie.writer or '').split(','))
        if director_match:
            score += WEIGHT_DIRECTOR
        if writer_match:
            score += WEIGHT_WRITER

        # Actors: threshold-based scoring for shared top N actors
        shared_actor_count = len(union_selected_top_actors.intersection(movie_top_actors)) if union_selected_top_actors and movie_top_actors else 0
        # threshold mapping: 0 -> 0, 1 -> 8, 2 -> 15, 3 -> 20 (approximate proportions of WEIGHT_ACTORS)
        actor_score = 0.0
        if shared_actor_count >= 3:
            actor_score = WEIGHT_ACTORS
        elif shared_actor_count == 2:
            actor_score = round(0.75 * WEIGHT_ACTORS, 2)  # 15
        elif shared_actor_count == 1:
            actor_score = round(0.4 * WEIGHT_ACTORS, 2)   # 8
        score += actor_score

        # Year proximity: linear scaling within YEAR_WINDOW
        if mean_selected_year and getattr(movie, 'year', None):
            try:
                diff = abs(int(movie.year) - mean_selected_year)
                if diff <= YEAR_WINDOW:
                    score += WEIGHT_YEAR * (1 - (diff / YEAR_WINDOW))
            except Exception:
                pass
        
        if score > 0:
            recommendations[movie.id] = score

    sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)

    # Store recommendations server-side and keep only a small token in the session
    token = str(uuid.uuid4())
    RECS_STORE[token] = sorted_recommendations
    session['recs_token'] = token

    return redirect(url_for('recommendations_list'))

@app.route('/recommendations')
def recommendations_list():
    """Displays paginated recommendations."""
    if 'recs_token' not in session:
        return redirect(url_for('home'))

    # We'll render the first page server-side (for SEO / no-JS fallback)
    page = request.args.get('page', 1, type=int)
    per_page = 10

    token = session.get('recs_token')
    all_recommendations = RECS_STORE.get(token)
    if not all_recommendations:
        return redirect(url_for('home'))
    total_pages = (len(all_recommendations) + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page
    paginated_recs_ids = [rec[0] for rec in all_recommendations[start:end]]

    # Fetch movie objects from the database based on the paginated IDs
    movies_dict = {movie.id: movie for movie in Movie.query.filter(Movie.id.in_(paginated_recs_ids)).all()}
    paginated_movies = [movies_dict[movie_id] for movie_id in paginated_recs_ids if movie_id in movies_dict]

    # Scores for the current page
    paginated_scores = {rec[0]: rec[1] for rec in all_recommendations[start:end]}

    return render_template(
        'recommendations.html',
        recommendations=paginated_movies,
        scores=paginated_scores,
        page=page,
        has_next=page < total_pages,
        per_page=per_page
    )


@app.route('/recommendations_data')
def recommendations_data():
    """Return a JSON page of recommendations for AJAX 'Show More' requests."""
    if 'recs_token' not in session:
        return jsonify({'error': 'no recommendations in session'}), 400

    page = request.args.get('page', 1, type=int)
    per_page = 10

    token = session.get('recs_token')
    all_recommendations = RECS_STORE.get(token)
    if not all_recommendations:
        return jsonify({'error': 'no recommendations stored on server'}), 400
    total_pages = (len(all_recommendations) + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page
    paginated = all_recommendations[start:end]
    paginated_ids = [rec[0] for rec in paginated]

    movies = Movie.query.filter(Movie.id.in_(paginated_ids)).all()
    movies_dict = {m.id: m for m in movies}

    results = []
    for rec_id, score in paginated:
        if rec_id in movies_dict:
            m = movies_dict[rec_id]
            results.append({
                'id': m.id,
                'title': m.title,
                'poster_url': m.poster_url,
                'score': score
            })

    return jsonify({
        'results': results,
        'page': page,
        'has_next': page < total_pages
    })

@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    """Renders the detail page for a single movie."""
    movie = Movie.query.get_or_404(movie_id)
    detailed_movie = None

    if movie.tmdb_id:
        detailed_movie = tmdb_movie_detail(movie.tmdb_id)

    if detailed_movie:
        # fallback to DB values when TMDb is missing specific fields
        detailed_movie.setdefault('description', movie.description)
        detailed_movie.setdefault('poster_url', movie.poster_url)
        detailed_movie.setdefault('director', movie.director)
        detailed_movie.setdefault('genre', movie.genre)
        detailed_movie.setdefault('year', movie.year)
        detailed_movie.setdefault('vote_average', movie.vote_average)
        detailed_movie.setdefault('vote_count', movie.vote_count)

        if not detailed_movie.get('actors_list') and movie.actors:
            detailed_movie['actors_list'] = [
                {
                    'name': actor.strip(),
                    'character': '',
                    'profile_url': 'https://via.placeholder.com/185x278.png?text=No+Photo'
                }
                for actor in movie.actors.split(',') if actor.strip()
            ]

        return render_template('movie_detail.html', movie=detailed_movie)

    # Fallback when TMDb data is unavailable
    fallback_movie = {
        'tmdb_id': movie.tmdb_id,
        'title': movie.title,
        'poster_url': movie.poster_url,
        'description': movie.description,
        'director': movie.director,
        'genre': movie.genre,
        'year': movie.year,
        'vote_average': movie.vote_average,
        'vote_count': movie.vote_count,
        'actors': movie.actors,
        'actors_list': []
    }

    if movie.actors:
        fallback_movie['actors_list'] = [
            {
                'name': actor.strip(),
                'character': '',
                'profile_url': 'https://via.placeholder.com/185x278.png?text=No+Photo'
            }
            for actor in movie.actors.split(',') if actor.strip()
        ]

    return render_template('movie_detail.html', movie=fallback_movie)


@app.route('/external_movie/<int:tmdb_id>')
def external_movie(tmdb_id):
    """Renders a movie detail fetched from TMDb API."""
    data = tmdb_movie_detail(tmdb_id)
    if not data:
        return redirect(url_for('home'))
    return render_template('movie_detail.html', movie=data)


@app.route('/upsert_tmdb', methods=['POST'])
def upsert_tmdb():
    """Given a tmdb_id, fetch movie from TMDb and insert or update DB record. Returns JSON {db_id}.
    """
    tmdb_id = request.json.get('tmdb_id') if request.is_json else request.form.get('tmdb_id')
    if not tmdb_id:
        return jsonify({'error': 'tmdb_id is required'}), 400

    try:
        tmdb_id = int(tmdb_id)
    except Exception:
        return jsonify({'error': 'invalid tmdb_id'}), 400

    # Try find existing
    movie = Movie.query.filter_by(tmdb_id=tmdb_id).first()
    if movie:
        return jsonify({'db_id': movie.id})

    # fetch from TMDb
    data = tmdb_movie_detail(tmdb_id)
    if not data:
        return jsonify({'error': 'tmdb fetch failed'}), 500

    # create new Movie row
    with app.app_context():
        m = Movie(
            title=data.get('title') or 'Unknown',
            description=data.get('description') or '',
            poster_url=data.get('poster_url') or 'https://via.placeholder.com/500x750.png?text=No+Image',
            genre=data.get('genre'),
            director=data.get('director'),
            writer=None,
            year=int(data.get('year')) if data.get('year') and data.get('year').isdigit() else None,
            actors=data.get('actors'),
            tmdb_id=tmdb_id,
            vote_average=data.get('vote_average'),
            vote_count=data.get('vote_count')
        )
        db.session.add(m)
        db.session.commit()
        return jsonify({'db_id': m.id})

if __name__ == '__main__':
    app.run(debug=True)
