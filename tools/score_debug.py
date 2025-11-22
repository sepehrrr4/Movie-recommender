import os, sys
# make sure project root is on sys.path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app
from models import Movie
from collections import defaultdict

# Copy of scoring config from app.py
WEIGHT_GENRE = 40
WEIGHT_DIRECTOR = 20
WEIGHT_WRITER = 10
WEIGHT_ACTORS = 20
WEIGHT_YEAR = 10
ACTORS_TOP_N = 3
YEAR_WINDOW = 5


def compute_score_for_candidate(selected_titles, candidate_title):
    with app.app_context():
        selected_movies = Movie.query.filter(Movie.title.in_(selected_titles)).all()
        candidate = Movie.query.filter(Movie.title==candidate_title).first()
        if not candidate:
            print('Candidate not found')
            return

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

        # candidate features
        movie_genres = set([g.strip() for g in (candidate.genre or '').split(',') if g.strip()])
        movie_actors = [a.strip() for a in (candidate.actors or '').split(',') if a.strip()]
        movie_top_actors = set(movie_actors[:ACTORS_TOP_N])

        breakdown = {}
        score = 0.0

        # Genre
        if union_selected_genres:
            shared_genres = union_selected_genres.intersection(movie_genres)
            if len(union_selected_genres) == 1:
                only_genre = next(iter(union_selected_genres))
                if only_genre not in movie_genres:
                    breakdown['genre'] = {'required_genre': only_genre, 'has_required': False, 'score': 0.0}
                    print('Candidate lacks required single genre -> total score 0')
                    print(breakdown)
                    return
            genre_fraction = len(shared_genres) / len(union_selected_genres)
            gscore = WEIGHT_GENRE * genre_fraction
            breakdown['genre'] = {'shared': list(shared_genres), 'fraction': genre_fraction, 'score': gscore}
            score += gscore
        else:
            breakdown['genre'] = {'shared': [], 'fraction': 0.0, 'score': 0.0}

        # Director / Writer: split weights
        director_match = candidate.director and candidate.director.strip() in selected_directors
        writer_match = getattr(candidate, 'writer', None) and any(w.strip() in selected_writers for w in (candidate.writer or '').split(','))
        dw_score = 0.0
        if director_match:
            dw_score += WEIGHT_DIRECTOR
        if writer_match:
            dw_score += WEIGHT_WRITER
        breakdown['director_writer'] = {'director_match': director_match, 'writer_match': writer_match, 'score': dw_score}
        score += dw_score

        # Actors: threshold-based scoring
        shared_actor_count = len(union_selected_top_actors.intersection(movie_top_actors)) if union_selected_top_actors else 0
        actor_score = 0.0
        if shared_actor_count >= 3:
            actor_score = WEIGHT_ACTORS
        elif shared_actor_count == 2:
            actor_score = round(0.75 * WEIGHT_ACTORS, 2)
        elif shared_actor_count == 1:
            actor_score = round(0.4 * WEIGHT_ACTORS, 2)
        breakdown['actors'] = {'shared_top_actors': list(union_selected_top_actors.intersection(movie_top_actors)), 'shared_count': shared_actor_count, 'score': actor_score}
        score += actor_score

        # Year
        yscore = 0.0
        if mean_selected_year and getattr(candidate, 'year', None):
            try:
                diff = abs(int(candidate.year) - mean_selected_year)
                if diff <= YEAR_WINDOW:
                    yscore = WEIGHT_YEAR * (1 - (diff / YEAR_WINDOW))
            except Exception:
                yscore = 0.0
        breakdown['year'] = {'candidate_year': candidate.year, 'mean_selected_year': mean_selected_year, 'score': yscore}
        score += yscore

        breakdown['total_score'] = score
        breakdown['candidate_title'] = candidate.title
        breakdown['candidate_id'] = candidate.id
        print(breakdown)


if __name__ == '__main__':
    # Example: check Spider-Man 3 and The Avengers vs Iron Man
    selected = ['Spider-Man 3', 'The Avengers']
    candidate = 'Iron Man'
    compute_score_for_candidate(selected, candidate)
