import os
from flask import Flask
from models import db, Movie

# --- Configuration ---
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# --- Dummy Movie Data ---
DUMMY_MOVIES = [
    {
        "title": "Inception",
        "description": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
        "poster_url": "https://m.media-amazon.com/images/I/81p+xe8cprL._AC_UF894,1000_QL80_.jpg",
        "genre": "Sci-Fi, Thriller",
        "director": "Christopher Nolan",
        "actors": "Leonardo DiCaprio, Joseph Gordon-Levitt, Elliot Page"
    },
    {
        "title": "The Matrix",
        "description": "A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.",
        "poster_url": "https://m.media-amazon.com/images/I/51EG732BV3L._AC_UF894,1000_QL80_.jpg",
        "genre": "Sci-Fi, Action",
        "director": "Lana Wachowski, Lilly Wachowski",
        "actors": "Keanu Reeves, Laurence Fishburne, Carrie-Anne Moss"
    },
    {
        "title": "Interstellar",
        "description": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
        "poster_url": "https://m.media-amazon.com/images/I/A1JVqNMI7UL._AC_UF894,1000_QL80_.jpg",
        "genre": "Sci-Fi, Adventure, Drama",
        "director": "Christopher Nolan",
        "actors": "Matthew McConaughey, Anne Hathaway, Jessica Chastain"
    },
    {
        "title": "The Dark Knight",
        "description": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
        "poster_url": "https://m.media-amazon.com/images/I/818hyMLtafL._AC_UF894,1000_QL80_.jpg",
        "genre": "Action, Crime, Drama",
        "director": "Christopher Nolan",
        "actors": "Christian Bale, Heath Ledger, Aaron Eckhart"
    },
    {
        "title": "Pulp Fiction",
        "description": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
        "poster_url": "https://m.media-amazon.com/images/I/71c05lTE0GL._AC_UF894,1000_QL80_.jpg",
        "genre": "Crime, Drama",
        "director": "Quentin Tarantino",
        "actors": "John Travolta, Uma Thurman, Samuel L. Jackson"
    },
    {
        "title": "Forrest Gump",
        "description": "The presidencies of Kennedy and Johnson, the Vietnam War, the Watergate scandal and other historical events unfold from the perspective of an Alabama man with an IQ of 75, whose only desire is to be reunited with his childhood sweetheart.",
        "poster_url": "https://m.media-amazon.com/images/I/61oZ3l6pTjL._AC_UF894,1000_QL80_.jpg",
        "genre": "Drama, Romance",
        "director": "Robert Zemeckis",
        "actors": "Tom Hanks, Robin Wright, Gary Sinise"
    },
    {
        "title": "The Shawshank Redemption",
        "description": "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
        "poster_url": "https://m.media-amazon.com/images/I/71715eBi1sL._AC_UF894,1000_QL80_.jpg",
        "genre": "Drama",
        "director": "Frank Darabont",
        "actors": "Tim Robbins, Morgan Freeman, Bob Gunton"
    },
    {
        "title": "Toy Story",
        "description": "A cowboy doll is profoundly threatened and jealous when a new spaceman figure supplants him as top toy in a boy's room.",
        "poster_url": "https://m.media-amazon.com/images/I/71a-2+5GqTL._AC_UF894,1000_QL80_.jpg",
        "genre": "Animation, Adventure, Comedy",
        "director": "John Lasseter",
        "actors": "Tom Hanks, Tim Allen, Don Rickles"
    },
    {
        "title": "The Lion King",
        "description": "Lion prince Simba and his father are targeted by his bitter uncle, who wants to ascend the throne himself.",
        "poster_url": "https://m.media-amazon.com/images/I/81C4s-3QJjL._AC_UF894,1000_QL80_.jpg",
        "genre": "Animation, Musical, Drama",
        "director": "Roger Allers, Rob Minkoff",
        "actors": "Matthew Broderick, Jeremy Irons, James Earl Jones"
    },
    {
        "title": "Gladiator",
        "description": "A former Roman General sets out to exact vengeance against the corrupt emperor who murdered his family and sent him into slavery.",
        "poster_url": "https://m.media-amazon.com/images/I/61C2343S0gL._AC_UF894,1000_QL80_.jpg",
        "genre": "Action, Adventure, Drama",
        "director": "Ridley Scott",
        "actors": "Russell Crowe, Joaquin Phoenix, Connie Nielsen"
    },
    {
        "title": "Saving Private Ryan",
        "description": "Following the Normandy Landings, a group of U.S. soldiers go behind enemy lines to retrieve a paratrooper whose brothers have been killed in action.",
        "poster_url": "https://m.media-amazon.com/images/I/81PEW+eFp0L._AC_UF894,1000_QL80_.jpg",
        "genre": "Drama, War",
        "director": "Steven Spielberg",
        "actors": "Tom Hanks, Matt Damon, Tom Sizemore"
    },
    {
        "title": "The Godfather",
        "description": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
        "poster_url": "https://m.media-amazon.com/images/I/714ZOEiVN2L._AC_UF894,1000_QL80_.jpg",
        "genre": "Crime, Drama",
        "director": "Francis Ford Coppola",
        "actors": "Marlon Brando, Al Pacino, James Caan"
    }
]

def seed_database():
    """Creates database tables and seeds them with movie data."""
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()

        for movie_data in DUMMY_MOVIES:
            movie = Movie(**movie_data)
            db.session.add(movie)
        
        db.session.commit()
        print("Database seeded with movies.")

if __name__ == '__main__':
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    seed_database()
