# Movie Recommendation System 🎬

A content-based movie recommendation system built with **Flask**, **Pandas**, and **Scikit-Learn**. This application suggests movies based on similarity logic using metadata from the TMDB 5000 dataset.

> **Note:** This project is currently in active development.

## 🚀 Features

* **Content-Based Filtering:** Recommends movies similar to a selected movie using TF-IDF vectorization and Cosine Similarity.
* **Database Integration:** Uses SQLite to store processed movie data for fast retrieval.
* **Clean UI:** Simple web interface to browse movies and view recommendations.
* **Data Processing:** Custom scripts to clean data and compute similarity matrices.

## 🛠️ Technologies Used

* **Backend:** Python, Flask, SQLAlchemy
* **Data Science:** Pandas, Scikit-Learn (for ML algorithms), Numpy
* **Frontend:** HTML5, CSS3 (Jinja2 templates)
* **Database:** SQLite

## 📦 Installation & Setup

Follow these steps to get the project running on your local machine:

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/sepehrrr4/movie-recommender.git](https://github.com/sepehrrr4/movie-recommender.git)
    cd movie-recommender
    ```

2.  **Create and activate a virtual environment (Optional but recommended):**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize Database & Compute Similarity:**
    Before running the app, you need to seed the database and calculate the similarity matrix.
    ```bash
    python seed_and_compute.py
    ```
    *(Note: Ensure `tmdb_5000_movies.csv` and `tmdb_5000_credits.csv` are in the root directory)*

5.  **Run the Application:**
    ```bash
    python app.py
    ```
    Access the app at `http://127.0.0.1:5000/`

## 🔮 Future Roadmap

This project is designed to be scalable. Here are the planned updates and features for upcoming versions:

* [ ] **Advanced Filtering:** Add search functionality by genre, year, and cast.
* [ ] **User Accounts:** Implementation of User Authentication (Login/Sign up).
* [ ] **Collaborative Filtering:** Implement user-based recommendations (e.g., "Users who liked this also liked...").
* [ ] **API Integration:** Fetch real-time data using the TMDB API instead of static CSVs.
* [ ] **UI/UX Improvements:** enhanced styling using Bootstrap or Tailwind CSS.
* [ ] **Deployment:** Dockerizing the app and deploying to a cloud provider (Heroku/Render).

## 🤝 Contributing

Contributions are welcome! If you have suggestions for improvements or bug fixes, please feel free to:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/YourFeature`).
3. Commit your changes.
4. Push to the branch and open a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
