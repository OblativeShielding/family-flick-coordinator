# run.py
# This script runs a couple startup checks, then
#   launches init and other scripts to load the webapp.

# library imports
from dotenv import load_dotenv
from flask import Flask, render_template
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

@app.route("/")
def home():
    return render_template("index.html")
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