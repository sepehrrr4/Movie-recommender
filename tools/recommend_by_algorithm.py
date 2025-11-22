import os, sys, json
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app
from models import Movie

def movie_to_dict(m):
    # convert SQLAlchemy Movie to dict following user's assumed structure
    def split_list(s):
        if not s:
            return []
        if isinstance(s, list):
            return s
        return [p.strip() for p in s.split(',') if p.strip()]

    return {
        'title': m.title,
        'genres': split_list(getattr(m, 'genre', None)),
        'director': getattr(m, 'director', None),
        'actors': split_list(getattr(m, 'actors', None)),
        'keywords': split_list(getattr(m, 'writer', None)),  # fallback: use writer as keywords if no keywords
        'imdb_rating': getattr(m, 'imdb_rating', None) if hasattr(m, 'imdb_rating') else None,
        'year': getattr(m, 'year', None)
    }

def score_candidate_against_seed(candidate, seed):
    score = 0
    # 1. Genre Match: +10 per shared genre
    shared_genres = set(candidate.get('genres', [])) & set(seed.get('genres', []))
    score += 10 * len(shared_genres)

    # 2. Director Match: +20
    if candidate.get('director') and seed.get('director') and candidate['director'].strip() == seed['director'].strip():
        score += 20

    # 3. Actor Match: +10 per shared actor
    shared_actors = set(candidate.get('actors', [])) & set(seed.get('actors', []))
    score += 10 * len(shared_actors)

    # 4. Keyword/Tag Match: +5 per shared keyword
    shared_kw = set(candidate.get('keywords', [])) & set(seed.get('keywords', []))
    score += 5 * len(shared_kw)

    # 5. Recency Bonus: +5 if within ±5 years
    try:
        cy = int(candidate.get('year')) if candidate.get('year') else None
        sy = int(seed.get('year')) if seed.get('year') else None
        if cy and sy and abs(cy - sy) <= 5:
            score += 5
    except Exception:
        pass

    return score

def aggregate_scores(candidates, seeds):
    results = []
    for c in candidates:
        if any(c['title'] == s['title'] for s in seeds):
            continue
        total = 0
        for s in seeds:
            total += score_candidate_against_seed(c, s)

        # Quality control penalty
        rating = c.get('imdb_rating')
        if rating is not None:
            try:
                if float(rating) < 6.0:
                    total = total * 0.5
            except Exception:
                pass

        results.append({'movie': c, 'raw_score': total})

    # scale raw_score to 1-100
    if not results:
        return []
    max_raw = max(r['raw_score'] for r in results) or 1
    for r in results:
        r['similarity_score'] = int(round((r['raw_score'] / max_raw) * 99)) + 1

    results.sort(key=lambda x: x['raw_score'], reverse=True)
    return results

def run(seed_titles):
    with app.app_context():
        # load all movies
        movies = Movie.query.all()
        movie_dicts = [movie_to_dict(m) for m in movies]

        # find seed movie dicts (by title exact match)
        seeds = []
        for t in seed_titles:
            found = next((m for m in movie_dicts if m['title'].lower() == t.lower()), None)
            if not found:
                print(f"Warning: seed movie '{t}' not found in DB")
            else:
                seeds.append(found)

        if len(seeds) == 0:
            print('No seeds found; aborting')
            return

        results = aggregate_scores(movie_dicts, seeds)
        top10 = results[:10]

        output = []
        rank = 1
        for r in top10:
            m = r['movie']
            output.append({
                'rank': rank,
                'title': m['title'],
                'year': m.get('year'),
                'similarity_score': r['similarity_score'],
                'reason_short': f"Shared genres/actors/keywords and year proximity"
            })
            rank += 1

        print(json.dumps(output, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    # default example if run directly
    seeds = sys.argv[1:] if len(sys.argv) > 1 else ['Inception', 'Shutter Island', 'The Matrix']
    run(seeds)
