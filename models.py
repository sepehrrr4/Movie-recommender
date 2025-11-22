from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    poster_url = db.Column(db.String(200), nullable=False)
    tmdb_id = db.Column(db.Integer, nullable=True)
    imdb_id = db.Column(db.String(20), nullable=True)
    genre = db.Column(db.String(100), nullable=True)
    director = db.Column(db.String(100), nullable=True)
    writer = db.Column(db.String(200), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    actors = db.Column(db.String(200), nullable=True)
    vote_average = db.Column(db.Float, nullable=True)
    vote_count = db.Column(db.Integer, nullable=True)

    def __repr__(self):
        return f'<Movie {self.title}>'

class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    source_movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    recommended_movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)

    source_movie = db.relationship('Movie', foreign_keys=[source_movie_id], backref='recommendations_made')
    recommended_movie = db.relationship('Movie', foreign_keys=[recommended_movie_id], backref='recommended_for')

    def __repr__(self):
        return f'<Recommendation {self.source_movie.title} -> {self.recommended_movie.title}>'
