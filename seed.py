import pandas as pd
import json
from app import app
from models import db, Movie

def seed_database():
    print("Reading CSV files...")
    try:
        movies_df = pd.read_csv('tmdb_5000_movies.csv')
        credits_df = pd.read_csv('tmdb_5000_credits.csv')
    except FileNotFoundError:
        print("Error: Make sure 'tmdb_5000_movies.csv' and 'tmdb_5000_credits.csv' are in the project folder.")
        return

    # To prevent a 'title' column conflict, we'll drop it from the credits dataframe.
    if 'title' in credits_df.columns:
        credits_df.drop('title', axis=1, inplace=True)

    # Merge the two dataframes based on the movie ID
    movies_df = movies_df.merge(credits_df, left_on='id', right_on='movie_id')

    # کد دیباگ را می‌توانید حذف یا کامنت کنید
    # print("DEBUG: Column names are:", movies_df.columns)

    print("Processing data and adding to database... This may take a few minutes.")
    with app.app_context():
        # حذف فیلم‌های قبلی برای جلوگیری از تکرار
        Movie.query.delete()
        db.session.commit()

        # تکرار روی هر ردیف از دیتافریم
        for index, row in movies_df.iterrows():
            # extract genres
            genres = []
            try:
                genres = [item.get('name') for item in json.loads(row['genres']) if item.get('name')]
            except Exception:
                genres = []

            # extract crew -> director and writers
            director = None
            writers = []
            try:
                crew = json.loads(row['crew'])
                director = next((item.get('name') for item in crew if item.get('job') == 'Director'), None)
                # common writer jobs
                for item in crew:
                    job = (item.get('job') or '').lower()
                    if 'writer' in job or 'screenplay' in job or 'author' in job or 'story' in job:
                        if item.get('name'):
                            writers.append(item.get('name'))
            except Exception:
                director = None

            # extract top 3 cast
            cast = []
            try:
                cast = [item.get('name') for item in json.loads(row['cast'])[:3] if item.get('name')]
            except Exception:
                cast = []

            # poster path if present
            poster_url = None
            if 'poster_path' in row and not pd.isna(row['poster_path']):
                poster_url = f"https://image.tmdb.org/t/p/w500{row['poster_path']}"
            if not poster_url:
                poster_url = "https://via.placeholder.com/500x750.png?text=No+Image"

            # year from release_date if possible
            year = None
            try:
                if 'release_date' in row and not pd.isna(row['release_date']):
                    year_str = str(row['release_date'])
                    if len(year_str) >= 4:
                        year = int(year_str[:4])
            except Exception:
                year = None

            # build movie object
            description = '' if pd.isna(row['overview']) else row['overview']
            movie = Movie(
                title=row['title'],
                description=description,
                poster_url=poster_url,
                genre=', '.join(genres),
                director=director,
                writer=', '.join(writers) if writers else None,
                year=year,
                actors=', '.join(cast)
            )
            db.session.add(movie)

        # کامیت کردن تغییرات در دیتابیس
        db.session.commit()

    print(f"Successfully added {len(movies_df)} movies to the database.")


if __name__ == '__main__':
    seed_database()