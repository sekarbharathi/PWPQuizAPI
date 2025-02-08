from app import app, db
from models.category import Category
from models.quiz import Quiz
from models.question import Question
from models.option import Option
from models.quiz_category import QuizCategory
from models.quiz_question import QuizQuestion

with app.app_context():
    db.create_all()  # Creates the tables based on models
    print("Database tables created!")
