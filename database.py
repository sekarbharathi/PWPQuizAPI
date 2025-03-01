"""
This module sets up the Flask application and initializes the database.

It configures the Flask app with the settings from the `Config` class in the `config.py` file.
The `db` instance from `models.py` is initialized and used to create the database tables.
"""
import os
from flask import Flask
from models import db  # Import db instance from models.py
from config import Config

# Get the base directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Initialize Flask app
app = Flask(__name__)

# Configure SQLAlchemy database
app.config.from_object(Config)

# Initialize SQLAlchemy with app
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")
