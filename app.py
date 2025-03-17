"""
This module defines a Flask application with various routes
for managing quizzes, categories, and questions.
It includes authentication using JWT, CRUD operations
for categories, quizzes, and questions, and integrates with a SQLAlchemy database.
"""
from urllib.parse import unquote
from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from sqlalchemy import func
import jsonschema
from jsonschema import validate
from flask_caching import Cache  # Import Flask-Caching
from config import Config
from models import db, Quiz, Category, Option, Question, QuizQuestion, QuizCategory
 
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
from flask_caching import Cache
 
# Flask-Caching setup
cache = Cache(app)
__all__ = ['app', 'db', 'cache']
 
# JWT setup
app.config["JWT_SECRET_KEY"] = "quiz-api-key"  # Replace with your secret key
jwt = JWTManager(app)
 
# Flask-Caching setup
# Use in-memory caching for simplicity
app.config["CACHE_TYPE"] = "SimpleCache"
# Cache timeout in seconds (5 minutes)
app.config["CACHE_DEFAULT_TIMEOUT"] = 300
cache = Cache(app)
 
# Define JSON schemas (unchanged)
login_schema = {
    "type": "object",
    "properties": {
        "username": {"type": "string"},
        "password": {"type": "string"}
    },
    "required": ["username", "password"]
}
 
category_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"}
    },
    "required": ["name"]
}
 
quiz_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "category_id": {"type": "integer"}
    },
    "required": ["name", "category_id"]
}
 
question_schema = {
    "type": "object",
    "properties": {
        "question_statement": {"type": "string"},
        "complex_level": {"type": "string"},
        "quiz_id": {"type": "integer"},
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "option_statement": {"type": "string"},
                    "is_correct": {"type": "boolean"}
                },
                "required": ["option_statement", "is_correct"]
            }
        }
    },
    "required": ["question_statement", "complex_level", "quiz_id", "options"]
}
 
# Helper function to validate JSON against schema (unchanged)
def validate_json(json_data, schema):
    """
    Validates the provided JSON data against the given JSON schema.
 
    Args:
        json_data (dict): The JSON data to validate.
        schema (dict): The JSON schema to validate the data against.
 
    Returns:
        tuple: A tuple containing a boolean indicating if the data is valid
               and an error message if validation fails.
    """
    try:
        validate(instance=json_data, schema=schema)
    except jsonschema.exceptions.ValidationError as err:
        return False, err.message
    return True, None
 
# Login endpoint (unchanged)
@app.route("/login", methods=["POST"])
def login():
    """
    Authenticates the user and generates an access token.
 
    This endpoint accepts a POST request with a JSON body containing
    'username' and 'password'. If the credentials match 'admin' and 'admin123',
    it returns an access token. Otherwise, it returns an error message.
 
    Returns:
        tuple: A tuple containing the JSON response with the token or error message
               and the corresponding HTTP status code.
    """
    data = request.json
    is_valid, error_message = validate_json(data, login_schema)
    if not is_valid:
        return jsonify({"msg": f"Invalid request: {error_message}"}), 400
 
    username = data.get("username")
    password = data.get("password")
 
    if username == "admin" and password == "admin123":  # Replace with your own auth logic
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
 
    return jsonify({"msg": "Invalid credentials"}), 401
 
# Category Endpoints
@app.route("/category", methods=["GET"])
@cache.cached(timeout=300)  # Cache the response for 5 minutes
def get_categories():
    """
    Retrieves all categories from the database.
 
    This endpoint returns a list of all categories stored in the database.
    The response is cached for 5 minutes to optimize performance.
 
    Returns:
        tuple: A tuple containing the JSON response with a list of categories
               and the HTTP status code 200.
    """
    categories = Category.query.all()
    categories_list = [{"category_id": cat.category_id,
                        "name": cat.name} for cat in categories]
    return jsonify(categories_list), 200
 
 
@app.route("/category", methods=["POST"])
@jwt_required()
def create_category():
    """
    Creates a new category in the database.
 
    This endpoint accepts a POST request with a JSON body containing
    the 'name' of the new category. Only users with an 'admin' role can
    create categories. The response will contain the unique_id of the created category.
 
    Returns:
        tuple: A tuple containing the JSON response with a success message,
               category unique_id, or error message, and the corresponding HTTP status code.
    """
    current_user = get_jwt_identity()
    if current_user != "admin":
        return jsonify({"msg": "Unauthorized"}), 403
 
    data = request.json
    is_valid, error_message = validate_json(data, category_schema)
    if not is_valid:
        return jsonify({"msg": f"Invalid request: {error_message}"}), 400
 
    name = data.get("name")
    new_category = Category(name=name)
    db.session.add(new_category)
    db.session.commit()
 
    # Invalidate the cache for categories
    cache.delete("view//category")
    return jsonify({"msg": "Category created", "unique_id": new_category.unique_id}), 201
 
 
@app.route("/category/<string:unique_id>", methods=["PUT"])
@jwt_required()
def update_category(unique_id):
    """
    Updates the details of an existing category.
 
    This endpoint accepts a PUT request with a JSON body containing the
    updated 'name' of the category. Only users with an 'admin' role can
    update categories. The category unique_id is passed as a URL parameter.
 
    Args:
        unique_id (str): The unique_id of the category to be updated.
 
    Returns:
        tuple: A tuple containing the JSON response with a success message
               or error message, and the corresponding HTTP status code.
    """
    current_user = get_jwt_identity()
    if current_user != "admin":
        return jsonify({"msg": "Unauthorized"}), 403
 
    data = request.json
    is_valid, error_message = validate_json(data, category_schema)
    if not is_valid:
        return jsonify({"msg": f"Invalid request: {error_message}"}), 400
 
    category = Category.query.filter_by(unique_id=unique_id).first()
    if not category:
        return jsonify({"msg": "Category not found"}), 404
 
    category.name = data.get("name", category.name)
    db.session.commit()
 
    # Invalidate the cache for categories
    cache.delete("view//category")
    return jsonify({"msg": "Category updated"}), 200
 
 
@app.route("/category/<string:unique_id>", methods=["DELETE"])
@jwt_required()
def delete_category(unique_id):
    """
    Deletes an existing category.
 
    This endpoint accepts a DELETE request to remove a category from the
    database. Only users with an 'admin' role can delete categories. The
    category unique_id is passed as a URL parameter.
 
    Args:
        unique_id (str): The unique_id of the category to be deleted.
 
    Returns:
        tuple: A tuple containing the JSON response with a success message
               or error message, and the corresponding HTTP status code.
    """
    current_user = get_jwt_identity()
    if current_user != "admin":
        return jsonify({"msg": "Unauthorized"}), 403
 
    category = Category.query.filter_by(unique_id=unique_id).first()
    if not category:
        return jsonify({"msg": "Category not found"}), 404
 
    db.session.delete(category)
    db.session.commit()
 
    # Invalidate the cache for categories
    cache.delete("view//category")
    return jsonify({"msg": "Category deleted"}), 200
 
# Quiz Endpoints
@app.route("/quiz", methods=["GET"])
@cache.cached(timeout=300)  # Cache the response for 5 minutes
def get_quizzes():
    """
    Retrieves all quizzes from the database.
 
    This endpoint returns a list of all quizzes stored in the database.
    The response is cached for 5 minutes to optimize performance.
 
    Returns:
        tuple: A tuple containing the JSON response with a list of quizzes
               and the HTTP status code 200.
    """
    quizzes = Quiz.query.all()
    quizzes_list = [{"unique_id": quiz.unique_id, "name": quiz.name,
                     "description": quiz.description} for quiz in quizzes]
    return jsonify(quizzes_list), 200
 
 
@app.route("/quiz", methods=["POST"])
@jwt_required()
def create_quiz():
    """
    Creates a new quiz in the database.
 
    This endpoint accepts a POST request with a JSON body containing the
    'name', 'description', and 'category_id' of the new quiz. Only users
    with an 'admin' role can create quizzes. The category must exist in the
    database.
 
    Returns:
        tuple: A tuple containing the JSON response with a success message,
               quiz unique_id, or error message, and the corresponding HTTP status code.
    """
    current_user = get_jwt_identity()
    if current_user != "admin":
        return jsonify({"msg": "Unauthorized"}), 403
 
    data = request.json
    is_valid, error_message = validate_json(data, quiz_schema)
    if not is_valid:
        return jsonify({"msg": f"Invalid request: {error_message}"}), 400
 
    name = data.get("name")
    description = data.get("description")
    category_id = data.get("category_id")
 
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"msg": "Category not found"}), 404
 
    new_quiz = Quiz(name=name, description=description)
    db.session.add(new_quiz)
    db.session.flush()
 
    new_quiz_category = QuizCategory(
        quiz_id=new_quiz.quiz_id,
        category_id=category_id)
    db.session.add(new_quiz_category)
    db.session.commit()
 
    # Invalidate the cache for quizzes
    cache.delete("view//quiz")
    return jsonify({"msg": "Quiz created", "unique_id": new_quiz.unique_id}), 201
 
 
@app.route("/quiz/<string:unique_id>", methods=["PUT"])
@jwt_required()
def update_quiz(unique_id):
    """
    Updates the details of an existing quiz.
 
    This endpoint accepts a PUT request with a JSON body containing the
    updated 'name', 'description', and 'category_id' of the quiz. Only
    users with an 'admin' role can update quizzes. The quiz unique_id is passed
    as a URL parameter.
 
    Args:
        unique_id (str): The unique_id of the quiz to be updated.
 
    Returns:
        tuple: A tuple containing the JSON response with a success message
               or error message, and the corresponding HTTP status code.
    """
    current_user = get_jwt_identity()
    if current_user != "admin":
        return jsonify({"msg": "Unauthorized"}), 403
 
    data = request.json
    is_valid, error_message = validate_json(data, quiz_schema)
    if not is_valid:
        return jsonify({"msg": f"Invalid request: {error_message}"}), 400
 
    quiz = Quiz.query.filter_by(unique_id=unique_id).first()
    if not quiz:
        return jsonify({"msg": "Quiz not found"}), 404
 
    quiz.name = data.get("name", quiz.name)
    quiz.description = data.get("description", quiz.description)
    new_category_id = data.get("category_id")
 
    if new_category_id:
        category = Category.query.get(new_category_id)
        if not category:
            return jsonify({"msg": "Category not found"}), 404
 
        QuizCategory.query.filter_by(quiz_id=quiz.quiz_id).delete()
        new_quiz_category = QuizCategory(
            quiz_id=quiz.quiz_id, category_id=new_category_id)
        db.session.add(new_quiz_category)
 
    db.session.commit()
 
    # Invalidate the cache for quizzes
    cache.delete("view//quiz")
    return jsonify({"msg": "Quiz updated"}), 200
 
 
@app.route("/quiz/<string:unique_id>", methods=["DELETE"])
@jwt_required()
def delete_quiz(unique_id):
    """
    Deletes an existing quiz.
 
    This endpoint accepts a DELETE request to remove a quiz from the
    database. Only users with an 'admin' role can delete quizzes. The
    quiz unique_id is passed as a URL parameter.
 
    Args:
        unique_id (str): The unique_id of the quiz to be deleted.
 
    Returns:
        tuple: A tuple containing the JSON response with a success message
               or error message, and the corresponding HTTP status code.
    """
    current_user = get_jwt_identity()
    if current_user != "admin":
        return jsonify({"msg": "Unauthorized"}), 403
 
    quiz = Quiz.query.filter_by(unique_id=unique_id).first()
    if not quiz:
        return jsonify({"msg": "Quiz not found"}), 404
 
    db.session.delete(quiz)
    db.session.commit()
 
    # Invalidate the cache for quizzes
    cache.delete("view//quiz")
    return jsonify({"msg": "Quiz deleted"}), 200
 
# Question and Options Endpoints
@app.route("/question", methods=["POST"])
@jwt_required()
def create_question():
    """
    Creates a new question along with its options and associates it with a quiz.
 
    This endpoint requires the user to be an admin (authenticated using JWT).
    The request must include the question statement, complexity level, quiz ID,
    and a list of options.
 
    Returns:
        JSON response with a success message and the unique_id of the created question.
        - 201: Question created successfully.
        - 400: Invalid request if the provided data is invalid.
        - 403: Unauthorized if the current user is not an admin.
        - 404: Quiz not found if the quiz ID does not exist.
    """
    current_user = get_jwt_identity()
    if current_user != "admin":
        return jsonify({"msg": "Unauthorized"}), 403
 
    data = request.json
    is_valid, error_message = validate_json(data, question_schema)
    if not is_valid:
        return jsonify({"msg": f"Invalid request: {error_message}"}), 400
 
    question_statement = data.get("question_statement")
    complex_level = data.get("complex_level")
    quiz_id = data.get("quiz_id")
    options = data.get("options", [])
 
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"msg": "Quiz not found"}), 404
 
    new_question = Question(
        question_statement=question_statement,
        complex_level=complex_level)
    db.session.add(new_question)
    db.session.flush()
    db.session.refresh(new_question)
 
    for opt in options:
        new_option = Option(
            option_statement=opt.get("option_statement"),
            is_correct=opt.get("is_correct", False),
            question_id=new_question.question_id
        )
        db.session.add(new_option)
 
    new_quiz_question = QuizQuestion(
        quiz_id=quiz_id,
        question_id=new_question.question_id)
    db.session.add(new_quiz_question)
    db.session.commit()
 
    return jsonify({"msg": "Question created", "unique_id": new_question.unique_id}), 201
 
 
@app.route("/question/<string:unique_id>", methods=["PUT"])
@jwt_required()
def update_question(unique_id):
    """
    Updates an existing question, its options, and its associated quiz.
 
    This endpoint requires the user to be an admin (authenticated using JWT).
    The request must include any updated fields for the question statement, complexity level,
    quiz ID, and a list of updated options.
 
    Args:
        unique_id (str): The unique_id of the question to update.
 
    Returns:
        JSON response with a success message.
        - 200: Question updated successfully.
        - 400: Invalid request if the provided data is invalid.
        - 403: Unauthorized if the current user is not an admin.
        - 404: Question not found if the question ID does not exist.
    """
    current_user = get_jwt_identity()
    if current_user != "admin":
        return jsonify({"msg": "Unauthorized"}), 403
 
    data = request.json
    is_valid, error_message = validate_json(data, question_schema)
    if not is_valid:
        return jsonify({"msg": f"Invalid request: {error_message}"}), 400
 
    question = Question.query.filter_by(unique_id=unique_id).first()
    if not question:
        return jsonify({"msg": "Question not found"}), 404
 
    question.question_statement = data.get(
        "question_statement", question.question_statement)
    question.complex_level = data.get("complex_level", question.complex_level)
 
    new_quiz_id = data.get("quiz_id")
    if new_quiz_id and new_quiz_id != QuizQuestion.query.filter_by(
            question_id=question.question_id).first().quiz_id:
        QuizQuestion.query.filter_by(question_id=question.question_id).delete()
        new_quiz_question = QuizQuestion(
            quiz_id=new_quiz_id, question_id=question.question_id)
        db.session.add(new_quiz_question)
 
    if "options" in data:
        Option.query.filter_by(question_id=question.question_id).delete()
        for opt in data["options"]:
            new_option = Option(
                option_statement=opt.get("option_statement"),
                is_correct=opt.get("is_correct", False),
                question_id=question.question_id
            )
            db.session.add(new_option)
 
    db.session.commit()
    return jsonify({"msg": "Question updated"}), 200
 
 
@app.route("/question", methods=["GET"])
def get_questions():
    """
    Retrieves a list of all questions, including their options and associated quiz IDs.
 
    Returns:
        JSON response containing a list of all questions.
        - 200: Successfully retrieves the list of questions.
    """
    questions = Question.query.all()
    question_list = []
    for q in questions:
        options = Option.query.filter_by(question_id=q.question_id).all()
        options_list = [{"unique_id": opt.unique_id,
                         "option_statement": opt.option_statement,
                         "is_correct": opt.is_correct} for opt in options]
 
        quiz_question = QuizQuestion.query.filter_by(
            question_id=q.question_id).first()
        quiz_id = quiz_question.quiz_id if quiz_question else None
 
        question_list.append({
            "unique_id": q.unique_id,
            "question_statement": q.question_statement,
            "complex_level": q.complex_level,
            "quiz_id": quiz_id,
            "options": options_list
        })
 
    return jsonify(question_list), 200
 
 
@app.route("/question/<string:unique_id>", methods=["GET"])
def get_question_by_id(unique_id):
    """
    Retrieves a specific question by its unique_id, along with its options and associated quiz ID.
 
    Args:
        unique_id (str): The unique_id of the question to retrieve.
 
    Returns:
        JSON response with the question details.
        - 200: Successfully retrieves the question.
        - 404: Question not found if the question ID does not exist.
    """
    question = Question.query.filter_by(unique_id=unique_id).first()
    if not question:
        return jsonify({"msg": "Question not found"}), 404
 
    options = Option.query.filter_by(question_id=question.question_id).all()
    options_list = [{"unique_id": opt.unique_id,
                     "option_statement": opt.option_statement,
                     "is_correct": opt.is_correct} for opt in options]
 
    quiz_question = QuizQuestion.query.filter_by(
        question_id=question.question_id).first()
    quiz_id = quiz_question.quiz_id if quiz_question else None
 
    question_data = {
        "unique_id": question.unique_id,
        "question_statement": question.question_statement,
        "complex_level": question.complex_level,
        "quiz_id": quiz_id,
        "options": options_list
    }
 
    return jsonify(question_data), 200
 
 
@app.route("/question/<string:unique_id>", methods=["DELETE"])
@jwt_required()
def delete_question(unique_id):
    """
    Deletes a specific question by its unique_id, along with its options and associated quiz records.
 
    This endpoint requires the user to be an admin (authenticated using JWT).
 
    Args:
        unique_id (str): The unique_id of the question to delete.
 
    Returns:
        JSON response with a success message.
        - 200: Question and related records deleted successfully.
        - 403: Unauthorized if the current user is not an admin.
        - 404: Question not found if the question ID does not exist.
    """
    current_user = get_jwt_identity()
    if current_user != "admin":
        return jsonify({"msg": "Unauthorized"}), 403
 
    question = Question.query.filter_by(unique_id=unique_id).first()
    if not question:
        return jsonify({"msg": "Question not found"}), 404
 
    QuizQuestion.query.filter_by(question_id=question.question_id).delete()
    Option.query.filter_by(question_id=question.question_id).delete()
    db.session.delete(question)
    db.session.commit()
 
    return jsonify({"msg": "Question and related records deleted"}), 200
 
# Filtering Endpoints
@app.route("/category/<category>/quiz/<quiz>/all", methods=["GET"])
def get_category_quiz_and_questions(category, quiz):
    """
    Retrieves all questions for a specific quiz under a given category.
 
    Args:
        category (str): The name of the category.
        quiz (str): The name of the quiz.
 
    Returns:
        JSON: A response containing the category name, quiz name, quiz description,
              and a list of questions with their options.
              Returns 404 if category or quiz is not found.
    """
    category = unquote(category)
    quiz = unquote(quiz)
 
    category_data = Category.query.filter(
        func.lower(Category.name) == category.lower()).first()
    if not category_data:
        return jsonify({"msg": "Category not found"}), 404
 
    quiz_data = Quiz.query.filter(
        func.lower(Quiz.name) == quiz.lower()).first()
    if not quiz_data:
        return jsonify({"msg": "Quiz not found"}), 404
 
    questions = db.session.query(Question).join(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_data.quiz_id
    ).all()
 
    if not questions:
        return jsonify({"msg": "No questions found"}), 404
 
    questions_list = []
    for q in questions:
        options = Option.query.filter_by(question_id=q.question_id).all()
        options_list = [{"unique_id": opt.unique_id,
                         "statement": opt.option_statement,
                         "is_correct": opt.is_correct} for opt in options]
 
        questions_list.append({
            "unique_id": q.unique_id,
            "question_statement": q.question_statement,
            "complex_level": q.complex_level,
            "options": options_list
        })
 
    return jsonify({
        "category": category_data.name,
        "quiz": quiz_data.name,
        "description": quiz_data.description,
        "questions": questions_list
    }), 200
 
 
@app.route("/category/<category>/quiz/<quiz>/questions", methods=["GET"])
def get_quiz_questions(category, quiz):
    """
    Retrieves a list of questions for a specific quiz under a given category with optional filters.
 
    Args:
        category (str): The name of the category.
        quiz (str): The name of the quiz.
 
    Returns:
        JSON: A response containing the quiz name and a list of questions with their options.
              Filters the questions by complexity level and number of questions.
              Returns 404 if category or quiz is not found.
    """
    category = unquote(category)
    quiz = unquote(quiz)
 
    question_count = request.args.get("question_count", default=5, type=int)
    complex_level = request.args.get(
        "complex_level", default="medium", type=str)
 
    category_data = Category.query.filter(
        func.lower(Category.name) == category.lower()).first()
    if not category_data:
        return jsonify({"msg": "Category not found"}), 404
 
    quiz_data = Quiz.query.filter(
        func.lower(Quiz.name) == quiz.lower()).first()
    if not quiz_data:
        return jsonify({"msg": "Quiz not found"}), 404
 
    questions = db.session.query(Question).join(QuizQuestion).filter(
        QuizQuestion.quiz_id == quiz_data.quiz_id,
        Question.complex_level == complex_level
    ).limit(question_count).all()
 
    if not questions:
        return jsonify({"msg": "No questions found"}), 404
 
    questions_list = []
    for q in questions:
        options = Option.query.filter_by(question_id=q.question_id).all()
        options_list = [{"unique_id": opt.unique_id,
                         "statement": opt.option_statement,
                         "is_correct": opt.is_correct} for opt in options]
 
        questions_list.append({
            "unique_id": q.unique_id,
            "question_statement": q.question_statement,
            "complex_level": q.complex_level,
            "options": options_list
        })
 
    return jsonify({"quiz": quiz, "questions": questions_list}), 200
 
 
@app.route("/quiz/category/<int:category_id>", methods=["GET"])
def get_quizzes_by_category(category_id):
    """
    Retrieves all quizzes for a given category ID.
 
    Args:
        category_id (int): The ID of the category.
 
    Returns:
        JSON: A response containing a list of quizzes under the specified category.
              Returns 404 if the category is not found.
    """
    category = Category.query.get(category_id)
    if not category:
        return jsonify({"msg": "Category not found"}), 404
 
    quizzes = db.session.query(Quiz).join(QuizCategory).filter(
        QuizCategory.category_id == category_id).all()
    quizzes_list = [{"unique_id": quiz.unique_id, "name": quiz.name,
                     "description": quiz.description} for quiz in quizzes]
 
    return jsonify(quizzes_list), 200
 
 
@app.route("/quiz/<string:unique_id>/questions", methods=["GET"])
def get_questions_by_quiz(unique_id):
    """
    Retrieves all questions for a specific quiz by quiz unique_id.
 
    Args:
        unique_id (str): The unique_id of the quiz.
 
    Returns:
        JSON: A response containing a list of questions for the specified quiz.
              Returns 404 if the quiz is not found.
    """
    quiz = Quiz.query.filter_by(unique_id=unique_id).first()
    if not quiz:
        return jsonify({"msg": "Quiz not found"}), 404
 
    questions = db.session.query(Question).join(
        QuizQuestion).filter(QuizQuestion.quiz_id == quiz.quiz_id).all()
    questions_list = []
    for q in questions:
        options = Option.query.filter_by(question_id=q.question_id).all()
        options_list = [{"unique_id": opt.unique_id,
                         "option_statement": opt.option_statement,
                         "is_correct": opt.is_correct} for opt in options]
        questions_list.append({
            "unique_id": q.unique_id,
            "question_statement": q.question_statement,
            "complex_level": q.complex_level,
            "options": options_list
        })
 
    return jsonify(questions_list), 200
 
 
if __name__ == "__main__":
    app.run(debug=True)
 