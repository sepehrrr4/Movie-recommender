from app import app, db

if __name__ == '__main__':
    with app.app_context():
        # Drop existing tables and recreate to pick up model changes (development only)
        db.drop_all()
        db.create_all()
        print('Database tables reset (dropped and created).')
