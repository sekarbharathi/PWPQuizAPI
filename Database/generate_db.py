from app import app,db
from models import Category, Quiz, Question, Option, QuizCategory, QuizQuestion
import random

def create_category(name):
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return category

def create_quiz(name, description, categories):
    quiz = Quiz(name=name, description=description)
    db.session.add(quiz)
    db.session.commit()
 
    # Create associations between quiz and categories
    for category in categories:
        quiz_category = QuizCategory(quiz_id=quiz.quiz_id, category_id=category.category_id)
        db.session.add(quiz_category)
    db.session.commit()
    return quiz
 
def create_question(question_statement, complex_level, quizzes):
    question = Question(question_statement=question_statement, complex_level=complex_level)
    db.session.add(question)
    db.session.commit()
 
    # Create associations between question and quizzes
    for quiz in quizzes:
        quiz_question = QuizQuestion(quiz_id=quiz.quiz_id, question_id=question.question_id)
        db.session.add(quiz_question)
    db.session.commit()
    return question
 

def create_option(question, option_statement, is_correct):
    option = Option(question_id=question.question_id, option_statement=option_statement, is_correct=is_correct)
    db.session.add(option)
    db.session.commit()
 
# Populate data
def populate_data():
    # Categories
    categories = [
        create_category("Math"),
        create_category("Science"),
        create_category("History"),
        create_category("Technology"),
        create_category("Literature")
    ]
 
    # Quizzes
    quizzes = [
        create_quiz("Math Quiz 1", "Basic Math Questions", [categories[0], categories[3]]),
        create_quiz("Science Quiz 1", "Basic Science Questions", [categories[1], categories[3]]),
        create_quiz("History Quiz 1", "Basic History Questions", [categories[2]]),
        create_quiz("Technology Quiz 1", "Basic Technology Questions", [categories[3], categories[4]]),
        create_quiz("Literature Quiz 1", "Basic Literature Questions", [categories[4]]),
        create_quiz("Math Quiz 2", "Advanced Math Questions", [categories[0]]),
        create_quiz("Science Quiz 2", "Advanced Science Questions", [categories[1]]),
        create_quiz("History Quiz 2", "Advanced History Questions", [categories[2]]),
        create_quiz("Technology Quiz 2", "Advanced Technology Questions", [categories[3]]),
        create_quiz("Literature Quiz 2", "Advanced Literature Questions", [categories[4]])
    ]
 
    # Questions and Options
    question_statements = [
        "What is 2 + 2?",
        "What is the chemical symbol for water?",
        "Who invented the telephone?",
        "What is the capital of France?",
        "Who wrote '1984'?",
        "What is the square root of 16?",
        "What is the atomic number of oxygen?",
        "Who developed the theory of relativity?",
        "What year did World War II end?",
        "What is the boiling point of water?"
    ]
 
    complex_levels = ["easy", "medium", "hard"]
 
    # Create questions and options
    questions = []
    for i in range(10):
        question = create_question(question_statements[i], random.choice(complex_levels), random.sample(quizzes, 3))
 
        # Add options
        create_option(question, "Option 1", True)
        create_option(question, "Option 2", False)
        create_option(question, "Option 3", False)
        create_option(question, "Option 4", False)
        questions.append(question)
 
if __name__ == "__main__":
    with app.app_context():
        populate_data()
    print("Database populated successfully!")