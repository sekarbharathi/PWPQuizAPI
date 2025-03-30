"""Configuration settings for the Flask application."""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Configuration settings for database and application behavior."""

    # pylint: disable=too-few-public-methods
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'database.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = 3600*24*7
