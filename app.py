"""
This module defines a Flask application with various routes
for managing quizzes, categories, and questions.
It includes authentication using JWT, CRUD operations
for categories, quizzes, and questions, and integrates with a SQLAlchemy database.
"""

from urllib.parse import unquote

from flask import Flask, request, jsonify
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


# Custom URL Converters
class CategoryConverter(BaseConverter):
    """Automatically handles URL encoding/decoding of category names."""

    def to_python(self, value):
        """Convert URL-encoded category name to Python string."""
        return unquote(value)

    def to_url(self, value):
        """Convert Python string to URL-safe category name."""
        return value


class QuizIDConverter(BaseConverter):
    """Validates quiz ID format (UUID-like)."""

    def to_python(self, value):
        """Convert and validate quiz ID."""
        if len(value) != 36:  # Simple format check
            raise ValueError("Invalid quiz ID format")
        return value


class QuizNameConverter(BaseConverter):
    """Handles quiz names (allows spaces and special chars)."""

    def to_python(self, value):
        """Convert URL-encoded quiz name to Python string."""
        return unquote(value)

    def to_url(self, value):
        """Convert Python string to URL-safe quiz name."""
        return value


class ComplexityConverter(BaseConverter):
    """Ensures only valid complexity levels are accepted"""

    def to_python(self, value):
        """Convert and validate complexity level."""
        value = value.lower()
        if value not in ["easy", "medium", "hard"]:
            raise ValueError("Invalid complexity level")
        return value


# Register all converters before defining any routes
app.url_map.converters["category"] = CategoryConverter
app.url_map.converters["quiz_id"] = QuizIDConverter
app.url_map.converters["quiz_name"] = QuizNameConverter
app.url_map.converters["complexity"] = ComplexityConverter

# JWT setup
app.config["JWT_SECRET_KEY"] = "quiz-api-key"
jwt = JWTManager(app)

# Flask-Caching setup
app.config["CACHE_TYPE"] = "SimpleCache"
app.config["CACHE_DEFAULT_TIMEOUT"] = 300
cache = Cache(app)

# List of objects to export

exported_objects = ["app", "db", "cache"]

# Define JSON schemas
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


def validate_json(json_data, schema):
    """Validates the provided JSON data against the given JSON schema."""
    try:
        validate(instance=json_data, schema=schema)
    except jsonschema.exceptions.ValidationError as err:
        return False, err.message
    return True, None


@app.before_request
def check_content_type():
    """Check content type for POST and PUT requests."""
    if request.method in ["POST", "PUT"]:
        if not request.is_json:
            return jsonify({"msg": "Missing JSON in request"}), 400
    return None


class LoginResource(MethodView):
    """Resource for handling user login and authentication."""

    def post(self):
        """Authenticates the user and generates an access token."""
        if not request.is_json:
            return jsonify({"msg": "Missing JSON in request"}), 400

        data = request.get_json()
        is_valid, error_message = validate_json(data, login_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        username = data.get("username")
        password = data.get("password")

        if username == "admin" and password == "admin123":
            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token), 200

        return jsonify({"msg": "Invalid credentials"}), 401


class CategoryResource(MethodView):
    """Resource for handling category operations."""

    decorators = [cache.cached(timeout=300)]

    def get(self):
        """Retrieves all categories from the database (names only)."""
        categories = Category.query.all()
        categories_list = [cat.name for cat in categories]
        return jsonify(categories_list), 200

    @jwt_required()
    def post(self):
        """Creates a new category in the database."""
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"msg": "Missing JSON in request"}), 400

        is_valid, error_message = validate_json(data, category_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        name = data.get("name").strip()

        if Category.query.filter(func.lower(Category.name) == name.lower()).first():
            return jsonify({"msg": "Category already exists"}), 400

        new_category = Category(name=name)
        db.session.add(new_category)
        db.session.commit()

        cache.delete("view//category")
        return jsonify({"msg": "Category created", "name": name}), 201


class CategoryDetailResource(MethodView):
    """Resource for handling specific category operations."""

    @jwt_required()
    def put(self, category_name):
        """Updates the details of an existing category."""
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"msg": "Missing JSON in request"}), 400

        is_valid, error_message = validate_json(data, category_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        category = Category.query.filter(
            func.lower(Category.name) == category_name.lower()
        ).first()

        if not category:
            return jsonify({"msg": "Category not found"}), 404

        new_name = data.get("name").strip()

        if Category.query.filter(
            func.lower(Category.name) == new_name.lower(),
            Category.category_id != category.category_id,
        ).first():
            return jsonify({"msg": "Category name already exists"}), 400

        category.name = new_name
        db.session.commit()

        cache.delete("view//category")
        return jsonify({"msg": "Category updated", "name": new_name}), 200

    @jwt_required()
    def delete(self, category_name):
        """Deletes an existing category."""
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        category = Category.query.filter(
            func.lower(Category.name) == category_name.lower()
        ).first()

        if not category:
            return jsonify({"msg": "Category not found"}), 404

        db.session.delete(category)
        db.session.commit()

        cache.delete("view//category")
        return jsonify({"msg": f"Category '{category.name}' deleted"}), 200


class QuizResource(MethodView):
    """Resource for handling quiz operations."""

    decorators = [cache.cached(timeout=300)]

    def get(self):
        """Retrieves all quizzes from the database."""
        quizzes = Quiz.query.all()
        quizzes_list = [
            {
                "unique_id": quiz.unique_id,
                "name": quiz.name,
                "description": quiz.description,
            }
            for quiz in quizzes
        ]
        return jsonify(quizzes_list), 200

    @jwt_required()
    def post(self):
        """Create a new quiz."""
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"msg": "Missing JSON in request"}), 400

        is_valid, error_message = validate_json(data, quiz_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        category_name = data.get("category_name").strip()
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
        return (
            jsonify(
                {
                    "msg": "Quiz created",
                    "unique_id": new_quiz.unique_id,
                    "category": category.name,
                }
            ),
            201,
        )


class QuizDetailResource(MethodView):
    """Resource for handling specific quiz operations."""

    @jwt_required()
    def put(self, unique_id):
        """Updates the details of an existing quiz."""
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"msg": "Missing JSON in request"}), 400

        is_valid, error_message = validate_json(data, quiz_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        quiz = Quiz.query.filter_by(unique_id=unique_id).first()
        if not quiz:
            return jsonify({"msg": "Quiz not found"}), 404

        quiz.name = data.get("name", quiz.name)
        quiz.description = data.get("description", quiz.description)

        if "category_name" in data:
            category_name = data.get("category_name").strip()
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
        return jsonify({"msg": "Quiz updated"}), 200

    @jwt_required()
    def delete(self, unique_id):
        """Deletes an existing quiz."""
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        quiz = Quiz.query.filter_by(unique_id=unique_id).first()
        if not quiz:
            return jsonify({"msg": "Quiz not found"}), 404

        db.session.delete(quiz)
        db.session.commit()

        cache.delete("view//quiz")
        return jsonify({"msg": "Quiz deleted"}), 200


class QuestionResource(MethodView):
    """Resource for handling question operations."""

    @jwt_required()
    def post(self):
        """Creates a new question along with its options."""
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"msg": "Missing JSON in request"}), 400

        is_valid, error_message = validate_json(data, question_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        question_statement = data.get("question_statement")
        complex_level = data.get("complex_level")
        quiz_unique_id = data.get("quiz_unique_id")
        options = data.get("options", [])

        quiz = Quiz.query.filter_by(unique_id=quiz_unique_id).first()
        if not quiz:
            return jsonify({"msg": "Quiz not found"}), 404

        new_question = Question(
            question_statement=question_statement, complex_level=complex_level
        )
        db.session.add(new_question)
        db.session.flush()
        db.session.refresh(new_question)

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

        return (
            jsonify({"msg": "Question created", "unique_id": new_question.unique_id}),
            201,
        )

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

            quiz_question = QuizQuestion.query.filter_by(
                question_id=q.question_id
            ).first()
            quiz_id = quiz_question.quiz_id if quiz_question else None

            question_list.append(
                {
                    "unique_id": q.unique_id,
                    "question_statement": q.question_statement,
                    "complex_level": q.complex_level,
                    "quiz_id": quiz_id,
                    "options": options_list,
                }
            )

        return jsonify(question_list), 200


class QuestionDetailResource(MethodView):
    """Resource for handling specific question operations."""

    def get(self, unique_id):
        """Retrieves a specific question by its unique_id."""
        question = Question.query.filter_by(unique_id=unique_id).first()
        if not question:
            return jsonify({"msg": "Question not found"}), 404

        options = Option.query.filter_by(question_id=question.question_id).all()
        options_list = [
            {
                "unique_id": opt.unique_id,
                "option_statement": opt.option_statement,
                "is_correct": opt.is_correct,
            }
            for opt in options
        ]

        quiz_question = QuizQuestion.query.filter_by(
            question_id=question.question_id
        ).first()
        quiz_id = quiz_question.quiz_id if quiz_question else None

        question_data = {
            "unique_id": question.unique_id,
            "question_statement": question.question_statement,
            "complex_level": question.complex_level,
            "quiz_id": quiz_id,
            "options": options_list,
        }

        return jsonify(question_data), 200

    @jwt_required()
    def put(self, unique_id):
        """Updates an existing question and its options."""
        current_user = get_jwt_identity()
        if current_user != "admin":
            return jsonify({"msg": "Unauthorized"}), 403

        data = request.get_json()
        if not data:
            return jsonify({"msg": "Missing JSON in request"}), 400

        is_valid, error_message = validate_json(data, question_schema)
        if not is_valid:
            return jsonify({"msg": f"Invalid request: {error_message}"}), 400

        question = Question.query.filter_by(unique_id=unique_id).first()
        if not question:
            return jsonify({"msg": "Question not found"}), 404

        question.question_statement = data.get(
            "question_statement", question.question_statement
        )
        question.complex_level = data.get("complex_level", question.complex_level)

        new_quiz_unique_id = data.get("quiz_unique_id")
        if new_quiz_unique_id:
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
            Option.query.filter_by(question_id=question.question_id).delete()
            for opt in data["options"]:
                new_option = Option(
                    option_statement=opt.get("option_statement"),
                    is_correct=opt.get("is_correct", False),
                    question_id=question.question_id,
                )
                db.session.add(new_option)

        db.session.commit()
        return jsonify({"msg": "Question updated"}), 200

    @jwt_required()
    def delete(self, unique_id):
        """Deletes a specific question and its related records."""
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


class CategoryQuizQuestionsResource(MethodView):
    """Resource for handling category-specific quiz questions."""

    def get(self, category, quiz):
        """Retrieves all questions for a specific quiz under a given category."""
        category_data = Category.query.filter(
            func.lower(Category.name) == category.lower()
        ).first()
        if not category_data:
            return jsonify({"msg": "Category not found"}), 404

        quiz_data = Quiz.query.filter(func.lower(Quiz.name) == quiz.lower()).first()
        if not quiz_data:
            return jsonify({"msg": "Quiz not found"}), 404

        questions = (
            db.session.query(Question)
            .join(QuizQuestion)
            .filter(QuizQuestion.quiz_id == quiz_data.quiz_id)
            .all()
        )

        if not questions:
            return jsonify({"msg": "No questions found"}), 404

        questions_list = []
        for q in questions:
            options = Option.query.filter_by(question_id=q.question_id).all()
            options_list = [
                {
                    "unique_id": opt.unique_id,
                    "statement": opt.option_statement,
                    "is_correct": opt.is_correct,
                }
                for opt in options
            ]

            questions_list.append(
                {
                    "unique_id": q.unique_id,
                    "question_statement": q.question_statement,
                    "complex_level": q.complex_level,
                    "options": options_list,
                }
            )

        return (
            jsonify(
                {
                    "category": category_data.name,
                    "quiz": quiz_data.name,
                    "description": quiz_data.description,
                    "questions": questions_list,
                }
            ),
            200,
        )


class FilteredQuizQuestionsResource(MethodView):
    """Resource for handling filtered quiz questions."""

    def get(self, category, quiz):
        """Retrieves filtered questions for a specific quiz."""
        question_count = request.args.get("question_count", default=5, type=int)
        complex_level = request.args.get("complex_level", default="medium", type=str)

        category_data = Category.query.filter(
            func.lower(Category.name) == category.lower()
        ).first()
        if not category_data:
            return jsonify({"msg": "Category not found"}), 404

        quiz_data = Quiz.query.filter(func.lower(Quiz.name) == quiz.lower()).first()
        if not quiz_data:
            return jsonify({"msg": "Quiz not found"}), 404

        questions = (
            db.session.query(Question)
            .join(QuizQuestion)
            .filter(
                QuizQuestion.quiz_id == quiz_data.quiz_id,
                Question.complex_level == complex_level,
            )
            .limit(question_count)
            .all()
        )

        if not questions:
            return jsonify({"msg": "No questions found"}), 404

        questions_list = []
        for q in questions:
            options = Option.query.filter_by(question_id=q.question_id).all()
            options_list = [
                {
                    "unique_id": opt.unique_id,
                    "statement": opt.option_statement,
                    "is_correct": opt.is_correct,
                }
                for opt in options
            ]

            questions_list.append(
                {
                    "unique_id": q.unique_id,
                    "question_statement": q.question_statement,
                    "complex_level": q.complex_level,
                    "options": options_list,
                }
            )

        return jsonify({"quiz": quiz, "questions": questions_list}), 200


class QuizByCategoryResource(MethodView):
    """Resource for handling quizzes by category."""

    def get(self, category_name):
        """Retrieves all quizzes for a given category name."""
        category = Category.query.filter(
            func.lower(Category.name) == category_name.lower()
        ).first()

        if not category:
            return jsonify({"msg": "Category not found"}), 404

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

        return jsonify(quizzes_list), 200


class QuestionsByQuizResource(MethodView):
    """Resource for handling questions by quiz."""

    def get(self, unique_id):
        """Retrieves all questions for a specific quiz."""
        quiz = Quiz.query.filter_by(unique_id=unique_id).first()
        if not quiz:
            return jsonify({"msg": "Quiz not found"}), 404

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
            questions_list.append(
                {
                    "unique_id": q.unique_id,
                    "question_statement": q.question_statement,
                    "complex_level": q.complex_level,
                    "options": options_list,
                }
            )

        return jsonify(questions_list), 200


# Register all routes with updated converters
app.add_url_rule("/login", view_func=LoginResource.as_view("login"), methods=["POST"])
app.add_url_rule(
    "/category", view_func=CategoryResource.as_view("category"), methods=["GET", "POST"]
)
app.add_url_rule(
    "/category/<category:category_name>",
    view_func=CategoryDetailResource.as_view("category_detail"),
    methods=["PUT", "DELETE"],
)
app.add_url_rule(
    "/quiz", view_func=QuizResource.as_view("quiz"), methods=["GET", "POST"]
)
app.add_url_rule(
    "/quiz/<quiz_id:unique_id>",
    view_func=QuizDetailResource.as_view("quiz_detail"),
    methods=["PUT", "DELETE"],
)
app.add_url_rule(
    "/question",
    view_func=QuestionResource.as_view("question"),
    methods=["GET", "POST"],
)
app.add_url_rule(
    "/question/<quiz_id:unique_id>",
    view_func=QuestionDetailResource.as_view("question_detail"),
    methods=["GET", "PUT", "DELETE"],
)
app.add_url_rule(
    "/category/<category:category>/quiz/<quiz_name:quiz>/all",
    view_func=CategoryQuizQuestionsResource.as_view("category_quiz_questions"),
    methods=["GET"],
)
app.add_url_rule(
    "/category/<category:category>/quiz/<quiz_name:quiz>/questions",
    view_func=FilteredQuizQuestionsResource.as_view("filtered_quiz_questions"),
    methods=["GET"],
)
app.add_url_rule(
    "/quiz/category/<category:category_name>",
    view_func=QuizByCategoryResource.as_view("quizzes_by_category"),
    methods=["GET"],
)
app.add_url_rule(
    "/quiz/<quiz_id:unique_id>/questions",
    view_func=QuestionsByQuizResource.as_view("questions_by_quiz"),
    methods=["GET"],
)

if __name__ == "__main__":
    app.run(debug=True)
