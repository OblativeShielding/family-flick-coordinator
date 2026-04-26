from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.engine import create_engine, URL
import os
import sys
import bcrypt

# -------------------------
# Load environment variables
# -------------------------
try:
    load_dotenv()
except Exception as e:
    print(f"ERROR: Unable to load .env. Make sure the file exists and is named properly.\n{e}")
    sys.exit(1)

# -------------------------
# Build database URL
# -------------------------
try:
    url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT")),
        database=os.getenv("MYSQL_DATABASE")
    )
except Exception as e:
    print(f"ERROR: Unable to create database URL. Make sure .env is formatted correctly.\n{e}")
    sys.exit(1)

# -------------------------
# Test database connection
# -------------------------
try:
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
except Exception as e:
    print(f"ERROR: Unable to connect to the database. Make sure .env has the correct values.\n{e}")
    sys.exit(1)

# -------------------------
# Flask app setup
# -------------------------
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = url.render_as_string(hide_password=False)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-change-this")
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

# -------------------------
# User model
# -------------------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

# -------------------------
# Create tables
# -------------------------
with app.app_context():
    db.create_all()

# -------------------------
# Routes
# -------------------------
@app.route("/")
def home():
    if "user_id" in session:
        user = User.query.get(session["user_id"])
        return render_template("home.html", user=user)
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        # Basic validation
        if not username or not email or not password or not confirm_password:
            flash("Please fill out all fields.")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect(url_for("register"))

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            flash("Username or email already exists.")
            return redirect(url_for("register"))

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful. Please log in.")
        return redirect(url_for("login"))

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
    # Get form data from movie_list.html modal
    title = (request.form.get("title") or "").strip()
    run_time = request.form.get("run_time", type=int)
    genre = (request.form.get("genre") or "").strip()
    image_url = (request.form.get("image_url") or "").strip()
    description = (request.form.get("description") or "").strip()
    rating = request.form.get("interest", type=int)

    # Basic backup/default values so the app does not break
    if not title:
        title = "Untitled Movie"

    if not run_time or run_time < 1:
        run_time = 100

    if not genre:
        genre = "Genre"

    if not rating:
        rating = 1

    # Create the next movie ID
    next_id = (max(MOVIES.keys()) + 1) if MOVIES else 1

    # Save the new movie into the temporary MOVIES dictionary
    MOVIES[next_id] = {
        "id": next_id,
        "title": title,
        "run_time": run_time,
        "genre": genre,

        # This is the important fix:
        # Save the description that came from the form.
        "description": description,

        "interest": max(1, min(5, rating)),
        "image_url": image_url,
    }

    return redirect(url_for("movie_list"))


@app.route("/movies/<int:movie_id>/edit", methods=["POST"])
def edit_movie(movie_id):
    # Find the movie being edited
    movie = MOVIES.get(movie_id)

    if movie is None:
        return "Movie not found", 404

    # Get updated form data from the edit modal
    title = (request.form.get("title") or "").strip()
    run_time = request.form.get("run_time", type=int)
    genre = (request.form.get("genre") or "").strip()
    image_url = (request.form.get("image_url") or "").strip()
    description = (request.form.get("description") or "").strip()
    rating = request.form.get("interest", type=int)

    # Only update title if the user typed something
    if title:
        movie["title"] = title

    # Only update runtime if it is a valid number
    if run_time and run_time > 0:
        movie["run_time"] = run_time

    # Only update genre if the user typed something
    if genre:
        movie["genre"] = genre

    # Image URL can be blank, so we always update it
    movie["image_url"] = image_url

    # This is the important fix:
    # Save the edited description into the movie dictionary.
    movie["description"] = description

    # Keep interest between 1 and 5 stars
    if rating:
        movie["interest"] = max(1, min(5, rating))

    # Send user to the movie details page after editing
    # so they can immediately see the updated description.
    return redirect(url_for("movie_details", movie_id=movie_id))


@app.route("/movies/<int:movie_id>/remove", methods=["POST"])
def remove_movie(movie_id):
    MOVIES.pop(movie_id, None)
    return redirect(url_for("movie_list"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.")
            return redirect(url_for("login"))

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(password.encode("utf-8"), user.password_hash.encode("utf-8")):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Login successful.")
            return redirect(url_for("home"))

        flash("Invalid email or password.")
        return redirect(url_for("login"))

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out.")
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)