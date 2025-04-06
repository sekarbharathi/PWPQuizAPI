"""
This module defines a Flask application with various routes
for managing quizzes, categories, and questions.
It includes authentication using JWT, CRUD operations
for categories, quizzes, and questions, and integrates with a SQLAlchemy database.
"""

from urllib.parse import unquote, quote

import uuid

from flask import Flask, request, jsonify, url_for
from flask.views import MethodView
from flask_jwt_extended import (
    JWTManager,
    jwt_required,
    create_access_token,
    get_jwt_identity,
)
from flask_caching import Cache

from werkzeug.routing import BaseConverter
from sqlalchemy import func
import jsonschema
from jsonschema import validate

from config import Config
from models import db, Quiz, Category, Option, Question, QuizQuestion, QuizCategory


app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


# Custom URL Converters with Database Integration
class CategoryConverter(BaseConverter):
    """Handles URL encoding/decoding and returns Category objects."""

    def to_python(self, value):
        """Convert URL-encoded category name to Category object."""
        name = unquote(value)
        category = Category.query.filter(
            func.lower(Category.name) == name.lower()
        ).first()

        print(f"Category name: {name}")
        if not category:
            raise ValueError(f"Category '{name}' not found")
        return category

    def to_url(self, value):
        """Convert Category object or name to URL-safe string."""
        if isinstance(value, Category):
            return value.name
        return str(value)


class QuizConverter(BaseConverter):
    """Handles quiz IDs and returns Quiz objects."""

    def to_python(self, value):
        """Convert and validate quiz ID to Quiz object."""
        try:
            # Attempt to validate as UUID
            uuid_obj = uuid.UUID(value)
            # If we get here, format is valid
        except (ValueError, AttributeError, TypeError):
            raise ValueError("Invalid quiz ID format")
            
        # Now check if quiz exists
        quiz = Quiz.query.filter_by(unique_id=value).first()
        if not quiz:
            raise ValueError(f"Quiz '{value}' not found")
        return quiz



    def to_url(self, value):
        """Convert Quiz object or ID to URL string."""
        if isinstance(value, Quiz):
            return value.unique_id
        return str(value)


class QuestionConverter(BaseConverter):
    """Handles question IDs and returns Question objects."""

    def to_python(self, value):
        """Convert and validate question ID to Question object."""
        question = Question.query.filter_by(unique_id=value).first()
        if not question:
            raise ValueError(f"Question '{value}' not found")
        return question

    def to_url(self, value):
        """Convert Question object or ID to URL string."""
        if isinstance(value, Question):
            return value.unique_id
        return str(value)


class ComplexityConverter(BaseConverter):
    """Ensures only valid complexity levels are accepted"""

    def to_python(self, value):
        """Convert and validate complexity level."""
        value = value.lower()
        if value not in ["easy", "medium", "hard"]:
            raise ValueError("Invalid complexity level")
        return value


class QuizNameConverter(BaseConverter):
    """Handles quiz names (allows spaces and special chars)."""

    def to_python(self, value):
        """Convert URL-encoded quiz name to Python string."""
        return unquote(value)

    def to_url(self, value):
        """Convert Python string to URL-safe quiz name."""
        return quote(value)


# Register all converters
app.url_map.converters["category"] = CategoryConverter
app.url_map.converters["quiz"] = QuizConverter
app.url_map.converters["question"] = QuestionConverter
app.url_map.converters["complexity"] = ComplexityConverter
app.url_map.converters['category_str'] = BaseConverter  # Simple string converter
app.url_map.converters['quiz_str'] = BaseConverter 

# JWT setup
app.config["JWT_SECRET_KEY"] = "quiz-api-key"
jwt = JWTManager(app)

# Flask-Caching setup
# Update Flask-Caching config
app.config['CACHE_TYPE'] = 'SimpleCache'
app.config['CACHE_DEFAULT_TIMEOUT'] = 300
app.config['CACHE_THRESHOLD'] = 100
app.config['CACHE_KEY_PREFIX'] = 'quiz_api_'
cache = Cache(app)

# List of objects to export
exported_objects = ["app", "db", "cache"]

# Define JSON schemas (unchanged)
login_schema = {
    "type": "object",
    "properties": {
        "username": {"type": "string"},
        "password": {"type": "string"},
    },
    "required": ["username", "password"],
}

category_schema = {
    "type": "object",
    "properties": {"name": {"type": "string"}},
    "required": ["name"],
}

quiz_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "description": {"type": "string"},
        "category_name": {"type": "string"},
    },
    "required": ["name", "category_name"],
}

question_schema = {
    "type": "object",
    "properties": {
        "question_statement": {"type": "string"},
        "complex_level": {"type": "string"},
        "quiz_unique_id": {"type": "string"},
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "option_statement": {"type": "string"},
                    "is_correct": {"type": "boolean"},
                },
                "required": ["option_statement", "is_correct"],
            },
        },
    },
    "required": ["question_statement", "complex_level", "quiz_unique_id", "options"],
}


@app.errorhandler(ValueError)
def handle_value_error(error):
    """Handle ValueError exceptions."""
    return jsonify({"msg": str(error)}), 404
def validate_json(json_data, schema):
    """Validates the provided JSON data against the given JSON schema."""
    try:
        validate(instance=json_data, schema=schema)
    except jsonschema.exceptions.ValidationError as err:
        return False, err.message
    return True, None

def add_hypermedia_links(data, resource_type, resource_id=None):
    """Add hypermedia links to API responses."""
    if isinstance(data, dict):
        links = {}
        
        # Add self link
        if resource_id:
            links["self"] = url_for(f"{resource_type}_detail", **{resource_type: resource_id}, _external=True)
        else:
            links["self"] = url_for(resource_type, _external=True)
            
        # Add collection link if we're looking at a specific resource
        if resource_id:
            links["collection"] = url_for(resource_type, _external=True)
            
        # Add resource-specific links
        if resource_type == "category" and resource_id:
            links["quizzes"] = url_for("quizzes_by_category", category=resource_id, _external=True)
        elif resource_type == "quiz" and resource_id:
            links["questions"] = url_for("questions_by_quiz", quiz=resource_id, _external=True)
            
        data["_links"] = links
    return data



@app.before_request
def check_content_type():
    """Check content type for POST and PUT requests."""
    if request.method in ["POST", "PUT"]:
        if not request.is_json:
            return jsonify({"msg": "Missing JSON in request"}), 400
    return None


# Resources with updated parameter handling
class LoginResource(MethodView):
    def post(self):
        """Authenticates the user and generates an access token."""
        data = request.get_json()
        is_valid, error_message = validate_json(data, login_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        username = data.get("username")
        password = data.get("password")

        if username == "admin" and password == "admin123":
            access_token = create_access_token(identity=username)
            response = {"access_token": access_token}
            return jsonify(add_hypermedia_links(response, "login")), 200

        return jsonify({"msg": "Invalid credentials"}), 401


class CategoryResource(MethodView):
    
    @cache.cached(timeout=300, key_prefix="view//category")
    def get(self):
        """Retrieves all categories from the database with hypermedia links."""
        categories = Category.query.all()
        
        # Create a list of categories with individual hypermedia links
        categories_data = []
        for cat in categories:
            # Create category data with basic info
            cat_data = {
                "name": cat.name,
                # Add hypermedia links specific to this category
                "_links": {
                    "self": url_for("category_detail", category=cat, _external=True),
                    "quizzes": url_for("quizzes_by_category", category=cat, _external=True)
                }
            }
            categories_data.append(cat_data)
        
        # Add collection-level hypermedia
        response = {
            "categories": categories_data,
            "_links": {
                "self": url_for("category", _external=True)
            }
        }
        
        return jsonify(response), 200
    @jwt_required()
    def post(self):
        """Creates a new category in the database."""
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        data = request.get_json()
        is_valid, error_message = validate_json(data, category_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        name = data.get("name").strip()

        # Check for existing category - directly query instead of using converter
        if Category.query.filter(func.lower(Category.name) == name.lower()).first():
            return jsonify({"msg": "Category already exists"}), 400
        # Check for empty name
        if not name:
            return jsonify({"msg": "Category name cannot be empty"}), 400

        new_category = Category(name=name)
        db.session.add(new_category)
        db.session.commit()

        cache.delete("view//category")
        response = {"msg": "Category created", "name": name}
        return jsonify(add_hypermedia_links(response, "category", name)), 201



class CategoryDetailResource(MethodView):
    def get(self, category):
        """Retrieves details of a specific category.
        
        The category parameter is already a Category object from the converter.
        """
        response = {
            "category_id": category.category_id,
            "name": category.name,
        }
        return jsonify(add_hypermedia_links(response, "category", category)), 200

    @jwt_required()
    def put(self, category):
        """Updates the details of an existing category.
        
        The category parameter is already a Category object from the converter.
        """
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        data = request.get_json()
        is_valid, error_message = validate_json(data, category_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        new_name = data.get("name").strip()

        # FIX: Using a direct query instead of reusing converter
        existing_category = Category.query.filter(
            func.lower(Category.name) == new_name.lower()
        ).first()
        
        if existing_category and existing_category.category_id != category.category_id:
            return jsonify({"msg": "Category name already exists"}), 400

        old_name = category.name
        category.name = new_name
        db.session.commit()
        cache.delete("view//category")
        response = {"msg": "Category updated", "old_name": old_name, "new_name": new_name}
        return jsonify(add_hypermedia_links(response, "category", category)), 200

    @jwt_required()
    def delete(self, category):
        """Deletes an existing category.
        
        The category parameter is already a Category object from the converter.
        """
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        category_name = category.name  # Store name before deletion
        
        # Check if category is in use by any quizzes - no need to query category again
        quiz_categories = QuizCategory.query.filter_by(category_id=category.category_id).first()
        
        if quiz_categories:
            return jsonify({"msg": "Cannot delete category in use by quizzes"}), 400

        db.session.delete(category)
        db.session.commit()

        cache.delete("view//category")
        response = {"msg": "Category deleted", "name": category_name}
        return jsonify(add_hypermedia_links(response, "category")), 200



class QuizResource(MethodView):
    @cache.cached(timeout=300, key_prefix="view//quiz")
    def get(self):
        """Retrieves all quizzes from the database with hypermedia links."""
        quizzes = Quiz.query.all()
        
        # Create a list of quizzes with individual hypermedia links
        quizzes_list = []
        for quiz in quizzes:
            # Create quiz data with basic info
            quiz_data = {
                "unique_id": quiz.unique_id,
                "name": quiz.name,
                "description": quiz.description,
                # Add hypermedia links specific to this quiz
                "_links": {
                    "self": url_for("quiz_detail", quiz=quiz, _external=True),
                    "questions": url_for("questions_by_quiz", quiz=quiz, _external=True)
                }
            }
            quizzes_list.append(quiz_data)
        
        # Add collection-level hypermedia
        response = {
            "quizzes": quizzes_list,
            "_links": {
                "self": url_for("quiz", _external=True)
            }
        }
        
        return jsonify(response), 200

    @jwt_required()
    def post(self):
        """Create a new quiz."""
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        data = request.get_json()
        is_valid, error_message = validate_json(data, quiz_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        category_name = data.get("category_name").strip()
        # Use direct query instead of converter
        category = Category.query.filter(
            func.lower(Category.name) == category_name.lower()
        ).first()

        if not category:
            return jsonify({"msg": "Category not found"}), 404

        new_quiz = Quiz(name=data.get("name"), description=data.get("description"))
        db.session.add(new_quiz)
        db.session.flush()

        new_quiz_category = QuizCategory(
            quiz_id=new_quiz.quiz_id, category_id=category.category_id
        )
        db.session.add(new_quiz_category)
        db.session.commit()

        cache.delete("view//quiz")
        response = {
            "msg": "Quiz created",
            "unique_id": new_quiz.unique_id,
            "category": category.name,
        }
        return jsonify(add_hypermedia_links(response, "quiz", new_quiz)), 201


class QuizDetailResource(MethodView):
    def get(self, quiz):
        """Retrieves details of a specific quiz.
        
        The quiz parameter is already a Quiz object from the converter.
        """
        # Get category for this quiz - using direct join instead of multiple queries
        quiz_category = QuizCategory.query.filter_by(quiz_id=quiz.quiz_id).first()
        category_name = None
        if quiz_category:
            category = db.session.get(Category, quiz_category.category_id)
            category_name = category.name if category else None
        
        response = {
            "unique_id": quiz.unique_id,
            "name": quiz.name,
            "description": quiz.description,
            "category": category_name
        }
        return jsonify(add_hypermedia_links(response, "quiz", quiz)), 200
        
    @jwt_required()
    def put(self, quiz):
        """Updates the details of an existing quiz.
        
        The quiz parameter is already a Quiz object from the converter.
        """
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        data = request.get_json()
        is_valid, error_message = validate_json(data, quiz_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        quiz.name = data.get("name", quiz.name)
        quiz.description = data.get("description", quiz.description)

        if "category_name" in data:
            category_name = data.get("category_name").strip()
            # Direct query instead of converter
            category = Category.query.filter(
                func.lower(Category.name) == category_name.lower()
            ).first()

            if not category:
                return jsonify({"msg": "Category not found"}), 404

            QuizCategory.query.filter_by(quiz_id=quiz.quiz_id).delete()
            new_quiz_category = QuizCategory(
                quiz_id=quiz.quiz_id, category_id=category.category_id
            )
            db.session.add(new_quiz_category)

        db.session.commit()
        cache.delete("view//quiz")
        response = {"msg": "Quiz updated"}
        return jsonify(add_hypermedia_links(response, "quiz", quiz)), 200

    @jwt_required()
    def delete(self, quiz):
        """Deletes an existing quiz.
        
        The quiz parameter is already a Quiz object from the converter.
        """
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        # Delete related records first - no need to query quiz again
        QuizCategory.query.filter_by(quiz_id=quiz.quiz_id).delete()
        
        # Get all questions for this quiz
        quiz_questions = QuizQuestion.query.filter_by(quiz_id=quiz.quiz_id).all()
        question_ids = [qq.question_id for qq in quiz_questions]
        
        # Delete quiz-question associations
        QuizQuestion.query.filter_by(quiz_id=quiz.quiz_id).delete()
        
        # Delete orphaned questions and their options
        for question_id in question_ids:
            # Check if question is used by other quizzes
            if not QuizQuestion.query.filter_by(question_id=question_id).first():
                Option.query.filter_by(question_id=question_id).delete()
                Question.query.filter_by(question_id=question_id).delete()
        
        # Finally delete the quiz
        db.session.delete(quiz)
        db.session.commit()

        cache.delete("view//quiz")
        response = {"msg": "Quiz deleted"}
        return jsonify(add_hypermedia_links(response, "quiz")), 200



class QuestionResource(MethodView):
    @jwt_required()
    def post(self):
        """Creates a new question along with its options."""
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        data = request.get_json()
        is_valid, error_message = validate_json(data, question_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        question_statement = data.get("question_statement")
        complex_level = data.get("complex_level")
        quiz_unique_id = data.get("quiz_unique_id")
        options = data.get("options", [])

        # Validate complex_level
        if complex_level not in ["easy", "medium", "hard"]:
            return jsonify({"msg": "Invalid complexity level"}), 400

        # Direct query instead of converter
        quiz = Quiz.query.filter_by(unique_id=quiz_unique_id).first()
        if not quiz:
            return jsonify({"msg": "Quiz not found"}), 404

        new_question = Question(
            question_statement=question_statement, complex_level=complex_level
        )
        db.session.add(new_question)
        db.session.flush()
        db.session.refresh(new_question)

        # Ensure at least one option is marked as correct
        has_correct_option = False
        if not options:
            return jsonify({"msg": "At least one option must be provided"}), 400
        for opt in options:
            if opt.get("is_correct", False):
                has_correct_option = True
                break
        
        if not has_correct_option and options:
            return jsonify({"msg": "At least one option must be marked as correct"}), 400

        for opt in options:
            new_option = Option(
                option_statement=opt.get("option_statement"),
                is_correct=opt.get("is_correct", False),
                question_id=new_question.question_id,
            )
            db.session.add(new_option)

        new_quiz_question = QuizQuestion(
            quiz_id=quiz.quiz_id, question_id=new_question.question_id
        )
        db.session.add(new_quiz_question)
        db.session.commit()

        response = {"msg": "Question created", "unique_id": new_question.unique_id}
        return jsonify(add_hypermedia_links(response, "question", new_question)), 201

    def get(self):
        """Retrieves a list of all questions with options."""
        questions = Question.query.all()
        question_list = []
        for q in questions:
            options = Option.query.filter_by(question_id=q.question_id).all()
            options_list = [
                {
                    "unique_id": opt.unique_id,
                    "option_statement": opt.option_statement,
                    "is_correct": opt.is_correct,
                }
                for opt in options
            ]

            # Use direct join to get quiz info
            quiz_question = QuizQuestion.query.filter_by(
                question_id=q.question_id
            ).first()

            quiz_unique_id = None
            if quiz_question:
                quiz = db.session.get(Quiz, quiz_question.quiz_id)
                quiz_unique_id = quiz.unique_id if quiz else None

            question_list.append(
                {
                    "unique_id": q.unique_id,
                    "question_statement": q.question_statement,
                    "complex_level": q.complex_level,
                    "quiz_unique_id": quiz_unique_id,
                    "options": options_list,
                }
            )

        response = {"questions": question_list}
        return jsonify(add_hypermedia_links(response, "question")), 200


class QuestionDetailResource(MethodView):
    def get(self, question):
        """Retrieves a specific question by its unique_id.
        
        The question parameter is already a Question object from the converter.
        """
        options = Option.query.filter_by(question_id=question.question_id).all()
        options_list = [
            {
                "unique_id": opt.unique_id,
                "option_statement": opt.option_statement,
                "is_correct": opt.is_correct,
            }
            for opt in options
        ]

        # Use direct join to get quiz info
        quiz_question = QuizQuestion.query.filter_by(
            question_id=question.question_id
        ).first()
        
        quiz_unique_id = None
        if quiz_question:
            quiz = db.session.get(Quiz, quiz_question.quiz_id)
            quiz_unique_id = quiz.unique_id if quiz else None

        question_data = {
            "unique_id": question.unique_id,
            "question_statement": question.question_statement,
            "complex_level": question.complex_level,
            "quiz_unique_id": quiz_unique_id,
            "options": options_list,
        }

        return jsonify(add_hypermedia_links(question_data, "question", question)), 200

    @jwt_required()
    def put(self, question):
        """Updates an existing question and its options.
        
        The question parameter is already a Question object from the converter.
        """
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        data = request.get_json()
        is_valid, error_message = validate_json(data, question_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        question.question_statement = data.get(
            "question_statement", question.question_statement
        )
        question.complex_level = data.get("complex_level", question.complex_level)

        # Validate complex_level
        if question.complex_level not in ["easy", "medium", "hard"]:
            return jsonify({"msg": "Invalid complexity level"}), 400

        new_quiz_unique_id = data.get("quiz_unique_id")
        if new_quiz_unique_id:
            # Direct query instead of converter
            new_quiz = Quiz.query.filter_by(unique_id=new_quiz_unique_id).first()
            if not new_quiz:
                return jsonify({"msg": "Quiz not found"}), 404

            current_quiz_question = QuizQuestion.query.filter_by(
                question_id=question.question_id
            ).first()
            if (
                not current_quiz_question
                or current_quiz_question.quiz_id != new_quiz.quiz_id
            ):
                QuizQuestion.query.filter_by(question_id=question.question_id).delete()
                new_quiz_question = QuizQuestion(
                    quiz_id=new_quiz.quiz_id, question_id=question.question_id
                )
                db.session.add(new_quiz_question)

        if "options" in data:
            # Ensure at least one option is marked as correct
            has_correct_option = False
            for opt in data["options"]:
                if opt.get("is_correct", False):
                    has_correct_option = True
                    break
                    
            if not has_correct_option and data["options"]:
                return jsonify({"msg": "At least one option must be marked as correct"}), 400
                
            Option.query.filter_by(question_id=question.question_id).delete()
            for opt in data["options"]:
                new_option = Option(
                    option_statement=opt.get("option_statement"),
                    is_correct=opt.get("is_correct", False),
                    question_id=question.question_id,
                )
                db.session.add(new_option)

        db.session.commit()
        response = {"msg": "Question updated"}
        return jsonify(add_hypermedia_links(response, "question", question)), 200

    @jwt_required()
    def delete(self, question):
        """Deletes a specific question and its related records.
        
        The question parameter is already a Question object from the converter.
        """
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        # No need to query question again
        QuizQuestion.query.filter_by(question_id=question.question_id).delete()
        Option.query.filter_by(question_id=question.question_id).delete()
        db.session.delete(question)
        db.session.commit()

        response = {"msg": "Question and related records deleted"}
        return jsonify(add_hypermedia_links(response, "question")), 200


class CategoryQuizQuestionsResource(MethodView):
    def get(self, category_name, quiz_name):  # Changed parameter names to be explicit
        """Retrieves all questions for a specific quiz under a given category."""
        # Get category by name (string)
        category = Category.query.filter(
            func.lower(Category.name) == category_name.lower()
        ).first()
        if not category:
            return jsonify({"msg": "Category not found"}), 404

        # Get quiz by name (string)
        quiz = Quiz.query.filter(
            func.lower(Quiz.name) == quiz_name.lower()
        ).first()
        if not quiz:
            return jsonify({"msg": "Quiz not found"}), 404

        # Verify quiz belongs to category
        quiz_category = QuizCategory.query.filter_by(
            quiz_id=quiz.quiz_id,
            category_id=category.category_id
        ).first()
        if not quiz_category:
            return jsonify({"msg": "Quiz not found in this category"}), 404

        # Get questions
        questions = (
            db.session.query(Question)
            .join(QuizQuestion)
            .filter(QuizQuestion.quiz_id == quiz.quiz_id)
            .all()
        )

        # Prepare response
        questions_list = []
        for q in questions:
            options = Option.query.filter_by(question_id=q.question_id).all()
            questions_list.append({
                "unique_id": q.unique_id,
                "question_statement": q.question_statement,
                "complex_level": q.complex_level,
                "options": [
                    {
                        "unique_id": opt.unique_id,
                        "statement": opt.option_statement,
                        "is_correct": opt.is_correct,
                    } for opt in options
                ]
            })

        return jsonify({
            "category": category.name,
            "quiz": quiz.name,
            "description": quiz.description,
            "questions": questions_list
        }), 200
class QuizByCategoryResource(MethodView):
    def get(self, category):
        """Retrieves all quizzes for a given category name.
        
        The category parameter is already a Category object from the converter.
        """
        # No need to query category again - use the provided category object
        quizzes = (
            db.session.query(Quiz)
            .join(QuizCategory)
            .filter(QuizCategory.category_id == category.category_id)
            .all()
        )

        quizzes_list = [
            {
                "unique_id": quiz.unique_id,
                "name": quiz.name,
                "description": quiz.description,
            }
            for quiz in quizzes
        ]

        response = {
            "category": category.name,
            "quizzes": quizzes_list
        }
        
        return jsonify(add_hypermedia_links(response, "category", category)), 200


class FilteredQuizQuestionsResource(MethodView):
    def get(self, category_name, quiz_name):
        """Retrieves filtered questions for a specific quiz with hypermedia."""
        # Get query parameters
        question_count = request.args.get('question_count', default=5, type=int)
        complex_level = request.args.get('complex_level', default='medium', type=str).lower()
        
        # Validate complexity level
        if complex_level not in ['easy', 'medium', 'hard']:
            return jsonify({"msg": "Invalid complexity level"}), 400

        # Get category by name
        category = Category.query.filter(
            func.lower(Category.name) == category_name.lower()
        ).first()
        if not category:
            return jsonify({"msg": "Category not found"}), 404

        # Get quiz by name
        quiz = Quiz.query.filter(
            func.lower(Quiz.name) == quiz_name.lower()
        ).first()
        if not quiz:
            return jsonify({"msg": "Quiz not found"}), 404

        # Verify quiz belongs to category
        quiz_category = QuizCategory.query.filter_by(
            quiz_id=quiz.quiz_id,
            category_id=category.category_id
        ).first()
        if not quiz_category:
            return jsonify({"msg": "Quiz not found in this category"}), 404

        # Get filtered questions
        questions = (
            db.session.query(Question)
            .join(QuizQuestion)
            .filter(
                QuizQuestion.quiz_id == quiz.quiz_id,
                Question.complex_level == complex_level
            )
            .order_by(func.random())  # Random ordering
            .limit(question_count)
            .all()
        )

        # Prepare response
        questions_list = []
        for q in questions:
            options = Option.query.filter_by(question_id=q.question_id).all()
            question_data = {
                "unique_id": q.unique_id,
                "question_statement": q.question_statement,
                "complex_level": q.complex_level,
                "options": [
                    {
                        "unique_id": opt.unique_id,
                        "statement": opt.option_statement,
                        "is_correct": opt.is_correct,
                    } for opt in options
                ],
                "_links": {
                    "self": url_for("question_detail", question=q, _external=True)
                }
            }
            questions_list.append(question_data)

        response = {
            "quiz": quiz.name,
            "complexity": complex_level,
            "question_count": len(questions_list),
            "questions": questions_list,
            "_links": {
                "self": url_for("filtered_quiz_questions", 
                               category_name=category_name, 
                               quiz_name=quiz_name, 
                               _external=True),
                "all_questions": url_for("category_quiz_questions", 
                                       category_name=category_name, 
                                       quiz_name=quiz_name, 
                                       _external=True),
                "category": url_for("category_detail", category=category, _external=True),
                "quiz": url_for("quiz_detail", quiz=quiz, _external=True)
            }
        }
        
        return jsonify(response), 200

    @jwt_required()
    def post(self, category_name, quiz_name):
        """Creates a new question for a specific quiz identified by category and quiz names."""
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        # Get category by name
        category = Category.query.filter(
            func.lower(Category.name) == category_name.lower()
        ).first()
        if not category:
            return jsonify({"msg": "Category not found"}), 404

        # Get quiz by name
        quiz = Quiz.query.filter(
            func.lower(Quiz.name) == quiz_name.lower()
        ).first()
        if not quiz:
            return jsonify({"msg": "Quiz not found"}), 404

        # Verify quiz belongs to category
        quiz_category = QuizCategory.query.filter_by(
            quiz_id=quiz.quiz_id,
            category_id=category.category_id
        ).first()
        if not quiz_category:
            return jsonify({"msg": "Quiz not found in this category"}), 404

        # Process the question data
        data = request.get_json()
        
        # Define a modified schema that doesn't require quiz_unique_id
        modified_question_schema = {
            "type": "object",
            "properties": {
                "question_statement": {"type": "string"},
                "complex_level": {"type": "string"},
                "options": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "option_statement": {"type": "string"},
                            "is_correct": {"type": "boolean"},
                        },
                        "required": ["option_statement", "is_correct"],
                    },
                },
            },
            "required": ["question_statement", "complex_level", "options"],
        }
        
        is_valid, error_message = validate_json(data, modified_question_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        question_statement = data.get("question_statement")
        complex_level = data.get("complex_level")
        options = data.get("options", [])

        # Validate complex_level
        if complex_level not in ["easy", "medium", "hard"]:
            return jsonify({"msg": "Invalid complexity level"}), 400

        # Create the new question
        new_question = Question(
            question_statement=question_statement, complex_level=complex_level
        )
        db.session.add(new_question)
        db.session.flush()
        db.session.refresh(new_question)

        # Ensure at least one option is marked as correct
        has_correct_option = False
        for opt in options:
            if opt.get("is_correct", False):
                has_correct_option = True
                break
                
        if not has_correct_option and options:
            return jsonify({"msg": "At least one option must be marked as correct"}), 400

        # Add options
        for opt in options:
            new_option = Option(
                option_statement=opt.get("option_statement"),
                is_correct=opt.get("is_correct", False),
                question_id=new_question.question_id,
            )
            db.session.add(new_option)

        # Create the quiz-question association
        new_quiz_question = QuizQuestion(
            quiz_id=quiz.quiz_id, question_id=new_question.question_id
        )
        db.session.add(new_quiz_question)
        db.session.commit()

        # Build response with hypermedia links
        response = {
            "msg": "Question created for quiz",
            "category": category.name,
            "quiz_name": quiz.name,
            "question_id": new_question.unique_id,
            "_links": {
                "self": url_for("filtered_quiz_questions", 
                                category_name=category_name, 
                                quiz_name=quiz_name, 
                                _external=True),
                "category": url_for("category", _external=True),
                "quiz": url_for("quiz", _external=True)
            }
        }
        
        return jsonify(response), 201




class QuestionsByQuizResource(MethodView):
    def get(self, quiz):  # Receives Quiz object
        """Retrieves all questions for a specific quiz with hypermedia links."""
        questions = (
            db.session.query(Question)
            .join(QuizQuestion)
            .filter(QuizQuestion.quiz_id == quiz.quiz_id)
            .all()
        )
        questions_list = []
        for q in questions:
            options = Option.query.filter_by(question_id=q.question_id).all()
            options_list = [
                {
                    "unique_id": opt.unique_id,
                    "option_statement": opt.option_statement,
                    "is_correct": opt.is_correct,
                }
                for opt in options
            ]
            
            # Add question-specific links
            question_data = {
                "unique_id": q.unique_id,
                "question_statement": q.question_statement,
                "complex_level": q.complex_level,
                "options": options_list,
                "_links": {
                    "self": url_for("question_detail", question=q, _external=True),
                    "quiz": url_for("quiz_detail", quiz=quiz, _external=True),
                }
            }
            questions_list.append(question_data)

        # Add collection-level hypermedia
        response = {
            "quiz": {
                "unique_id": quiz.unique_id,
                "name": quiz.name,
            },
            "questions": questions_list,
            "_links": {
                "self": url_for("questions_by_quiz", quiz=quiz, _external=True),
                "quiz": url_for("quiz_detail", quiz=quiz, _external=True),
            }
        }
        
        return jsonify(response), 200



# Register all routes with updated converters
app.add_url_rule("/login", view_func=LoginResource.as_view("login"), methods=["POST"])
app.add_url_rule(
    "/category", view_func=CategoryResource.as_view("category"), methods=["GET", "POST"]
)
app.add_url_rule(
    "/category/<category:category>",
    view_func=CategoryDetailResource.as_view("category_detail"),
    methods=["GET","PUT", "DELETE"],
)
app.add_url_rule(
    "/quiz", view_func=QuizResource.as_view("quiz"), methods=["GET", "POST"]
)
app.add_url_rule(
    "/quiz/<quiz:quiz>",
    view_func=QuizDetailResource.as_view("quiz_detail"),
    methods=["GET","PUT", "DELETE"],
)
app.add_url_rule(
    "/question",
    view_func=QuestionResource.as_view("question"),
    methods=["GET", "POST"],
)
app.add_url_rule(
    "/question/<question:question>",
    view_func=QuestionDetailResource.as_view("question_detail"),
    methods=["GET", "PUT", "DELETE"],
)
app.add_url_rule(
    '/category/<category_str:category_name>/quiz/<quiz_str:quiz_name>/all',
    view_func=CategoryQuizQuestionsResource.as_view('category_quiz_questions'),
    methods=['GET']
)
app.add_url_rule(
    '/category/<category_str:category_name>/quiz/<quiz_str:quiz_name>/questions',
    view_func=FilteredQuizQuestionsResource.as_view('filtered_quiz_questions'),
    methods=['GET','POST']
)
app.add_url_rule(
    "/category/<category:category>/quizzes",
    view_func=QuizByCategoryResource.as_view("quizzes_by_category"),
    methods=["GET"],
)
app.add_url_rule(
    "/quiz/<quiz:quiz>/questions",
    view_func=QuestionsByQuizResource.as_view("questions_by_quiz"),
    methods=["GET"],
)

if __name__ == "__main__":
    app.run(debug=True)
