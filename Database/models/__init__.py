from .category import Category
from .quiz import Quiz
from .question import Question
from .option import Option
from .quiz_category import QuizCategory 
from .quiz_question import QuizQuestion
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
