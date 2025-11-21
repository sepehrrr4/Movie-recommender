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
            # استخراج ژانرها
            genres = [item['name'] for item in json.loads(row['genres'])]

            # استخراج کارگردان
            crew = json.loads(row['crew'])
            director = next((item['name'] for item in crew if item['job'] == 'Director'), None)

            # استخراج ۳ بازیگر اصلی
            cast = [item['name'] for item in json.loads(row['cast'])[:3]]

            # چون ستون پوستر وجود ندارد، یک URL جایگزین قرار می‌دهیم
            poster_url = "https://via.placeholder.com/500x750.png?text=No+Image"

            # ساخت شیء فیلم
            description = '' if pd.isna(row['overview']) else row['overview']
            movie = Movie(
                title=row['title'],
                description=description,
                poster_url=poster_url,
                genre=', '.join(genres),
                director=director,
                actors=', '.join(cast)
            )
            db.session.add(movie)

        # کامیت کردن تغییرات در دیتابیس
        db.session.commit()

    print(f"Successfully added {len(movies_df)} movies to the database.")


if __name__ == '__main__':
    seed_database()