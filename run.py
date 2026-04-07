# run.py
# This script runs a couple startup checks, then
#   launches init and other scripts to load the webapp.

# library imports
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from sqlalchemy import text
from sqlalchemy.engine import create_engine, URL
import sys

# check for env
try:
    load_dotenv()
except Exception as e:
    print(f"ERROR: Unable to load .env. Make sure the file exists and is named properly.\n{e}")
    sys.exit(1)

# try to assemble the SQL address
try:
    url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        host=os.getenv("MYSQL_HOST"),
        port=os.getenv("MYSQL_PORT"),
        database=os.getenv("MYSQL_DATABASE")
    )
except Exception as e:
    print(f"ERROR: Unable to create database URL. Make sure .env is formatted correctly.\n{e}")
    sys.exit(1)

# try to connect to the database
try:
    # create the engine
    engine = create_engine(url)
    # execute a query
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as e:
    print(f"ERROR: Unable to connect to the database. Make sure .env has the correct values.\n{e}")
    sys.exit(1)

# start the server
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = url

db = SQLAlchemy(app)

# Temporary in-memory data for UI testing.
MOVIES = {
    1: {
        "id": 1,
        "title": "Minecraft Movie",
        "run_time": 101,
        "genre": "Adventure/Comedy",
        "description": "A simple placeholder description for the first movie option.",
        "interest": 3,
        "image_url": "",
    }
}

@app.route("/")
def home():
    return render_template("login.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/movies")
def movie_list():
    return render_template("movie_list.html", movies=list(MOVIES.values()))


@app.route("/movies/<int:movie_id>")
def movie_details(movie_id):
    movie = MOVIES.get(movie_id)
    if movie is None:
        return "Movie not found", 404
    return render_template("movie_details.html", movie=movie)


@app.route("/movies/add", methods=["POST"])
def add_movie():
    title = (request.form.get("title") or "").strip()
    run_time = request.form.get("run_time", type=int)
    genre = (request.form.get("genre") or "").strip()
    image_url = (request.form.get("image_url") or "").strip()
    rating = request.form.get("interest", type=int)

    if not title:
        title = "Untitled Movie"
    if not run_time or run_time < 1:
        run_time = 100
    if not genre:
        genre = "Genre"
    if not rating:
        rating = 1

    next_id = (max(MOVIES.keys()) + 1) if MOVIES else 1
    MOVIES[next_id] = {
        "id": next_id,
        "title": title,
        "run_time": run_time,
        "genre": genre,
        "description": "Simple placeholder description.",
        "interest": max(1, min(5, rating)),
        "image_url": image_url,
    }
    return redirect(url_for("movie_list"))


@app.route("/movies/<int:movie_id>/edit", methods=["POST"])
def edit_movie(movie_id):
    movie = MOVIES.get(movie_id)
    if movie is None:
        return "Movie not found", 404

    title = (request.form.get("title") or "").strip()
    run_time = request.form.get("run_time", type=int)
    genre = (request.form.get("genre") or "").strip()
    image_url = (request.form.get("image_url") or "").strip()
    rating = request.form.get("interest", type=int)

    if title:
        movie["title"] = title
    if run_time and run_time > 0:
        movie["run_time"] = run_time
    if genre:
        movie["genre"] = genre
    movie["image_url"] = image_url
    if rating:
        movie["interest"] = max(1, min(5, rating))

    return redirect(url_for("movie_list"))


@app.route("/movies/<int:movie_id>/remove", methods=["POST"])
def remove_movie(movie_id):
    MOVIES.pop(movie_id, None)
    return redirect(url_for("movie_list"))
'''
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))

@app.route("/users")
def users():
    return {"users": [u.name for u in User.query.all()]}
'''

if __name__ == "__main__":
    app.run(debug=True)