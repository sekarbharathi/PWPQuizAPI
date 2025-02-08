from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

from models.category import Category
from models.quiz import Quiz
from models.question import Question
from models.option import Option

if __name__ == "__main__":
    app.run(debug=True)
