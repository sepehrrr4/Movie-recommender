from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from models import db, Movie
from collections import defaultdict
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)
db.init_app(app)

@app.route('/')
def home():
    """Renders the home page with a list of all movies."""
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)

@app.route('/search')
def search():
    """Searches for movies based on a query string and returns JSON."""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    search_results = Movie.query.filter(Movie.title.ilike(f'%{query}%')).limit(10).all()
    results = [{'id': movie.id, 'title': movie.title} for movie in search_results]
    return jsonify(results)

@app.route('/recommend', methods=['POST'])
def recommend():
    """Calculates and stores recommendations in the session, then redirects."""
    selected_movie_ids = request.form.getlist('movies')
    if not selected_movie_ids or len(selected_movie_ids) > 3:
        return "Please select up to three movies.", 400

    selected_movies = Movie.query.filter(Movie.id.in_(selected_movie_ids)).all()

    recommendations = defaultdict(float)
    for movie in Movie.query.filter(Movie.id.notin_(selected_movie_ids)).all():
        score = 0
        for selected_movie in selected_movies:
            if selected_movie.genre and movie.genre:
                selected_genres = set(g.strip() for g in selected_movie.genre.split(','))
                movie_genres = set(g.strip() for g in movie.genre.split(','))
                score += len(selected_genres.intersection(movie_genres))
            if selected_movie.director and movie.director and selected_movie.director == movie.director:
                score += 5
            if selected_movie.actors and movie.actors:
                selected_actors = set(a.strip() for a in selected_movie.actors.split(','))
                movie_actors = set(a.strip() for a in movie.actors.split(','))
                score += len(selected_actors.intersection(movie_actors))
        
        if score > 0:
            recommendations[movie.id] = score

    sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
    session['recommendations'] = sorted_recommendations
    
    return redirect(url_for('recommendations_list'))

@app.route('/recommendations')
def recommendations_list():
    """Displays paginated recommendations."""
    if 'recommendations' not in session:
        return redirect(url_for('home'))

    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    all_recommendations = session['recommendations']
    total_pages = (len(all_recommendations) + per_page - 1) // per_page
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_recs_ids = [rec[0] for rec in all_recommendations[start:end]]
    
    # Fetch movie objects from the database based on the paginated IDs
    # We use a dictionary to preserve the order from the recommendations list
    movies_dict = {movie.id: movie for movie in Movie.query.filter(Movie.id.in_(paginated_recs_ids)).all()}
    paginated_movies = [movies_dict[movie_id] for movie_id in paginated_recs_ids if movie_id in movies_dict]

    # We also need to pass the scores for the current page
    paginated_scores = {rec[0]: rec[1] for rec in all_recommendations[start:end]}

    return render_template(
        'recommendations.html',
        recommendations=paginated_movies,
        scores=paginated_scores,
        page=page,
        has_next=page < total_pages
    )

@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id):
    """Renders the detail page for a single movie."""
    movie = Movie.query.get_or_404(movie_id)
    return render_template('movie_detail.html', movie=movie)

if __name__ == '__main__':
    app.run(debug=True)
