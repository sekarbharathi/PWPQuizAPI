"""Database models for the Quiz API application."""

import uuid

from flask_sqlalchemy import SQLAlchemy

import sqlalchemy as sa

# Initialize SQLAlchemy instance

db = SQLAlchemy()


class Category(db.Model):

    """Represents a category for quizzes."""

    # pylint: disable=too-few-public-methods

    category_id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    # Relationship to Quiz via junction table

    quizzes = db.relationship(

        'Quiz',

        secondary='quiz_category',

        backref='categories',

        cascade="all, delete"

    )


class Option(db.Model):

    """Represents an answer option for a question."""

    # pylint: disable=too-few-public-methods

    option_id = db.Column(db.Integer, primary_key=True)

    unique_id = db.Column(

        db.String(36),

        default=lambda: str(uuid.uuid4()),

        unique=True,

        nullable=False

    )

    option_statement = db.Column(db.String(500), nullable=False)

    is_correct = db.Column(db.Boolean, nullable=False)

    question_id = db.Column(

        db.Integer,

        db.ForeignKey('question.question_id', ondelete="CASCADE"),

        nullable=False

    )


class QuizCategory(db.Model):

    """Junction table for mapping quizzes to categories."""

    # pylint: disable=too-few-public-methods

    __tablename__ = 'quiz_category'

    quiz_id = db.Column(

        db.Integer,

        db.ForeignKey('quiz.quiz_id', ondelete="CASCADE"),

        primary_key=True

    )

    unique_id = db.Column(

        db.String(36),

        default=lambda: str(uuid.uuid4()),

        unique=True,

        nullable=False

    )

    category_id = db.Column(

        db.Integer,

        db.ForeignKey('category.category_id', ondelete="CASCADE"),

        primary_key=True

    )


class Question(db.Model):

    """Represents a question in the quiz system."""

    # pylint: disable=too-few-public-methods

    question_id = db.Column(db.Integer, primary_key=True)

    unique_id = db.Column(

        db.String(36),

        default=lambda: str(uuid.uuid4()),

        unique=True,

        nullable=False

    )

    question_statement = db.Column(db.String(500), nullable=False)

    complex_level = db.Column(db.String(20), nullable=False)

    __table_args__ = (

        sa.CheckConstraint(

            "complex_level IN ('easy', 'medium', 'hard')",

            name="check_complex_level"

        ),

    )

    # Relationship to Option (Multiple options per question)

    options = db.relationship(

        'Option',

        backref='question',

        cascade="all, delete-orphan"

    )


class QuizQuestion(db.Model):

    """Junction table for mapping quizzes to questions."""

    # pylint: disable=too-few-public-methods

    __tablename__ = 'quiz_question'

    quiz_id = db.Column(

        db.Integer,

        db.ForeignKey('quiz.quiz_id', ondelete="CASCADE"),

        primary_key=True

    )

    unique_id = db.Column(

        db.String(36),

        default=lambda: str(uuid.uuid4()),

        unique=True,

        nullable=False

    )

    question_id = db.Column(

        db.Integer,

        db.ForeignKey('question.question_id', ondelete="CASCADE"),

        primary_key=True

    )


class Quiz(db.Model):

    """Represents a quiz containing multiple questions."""

    # pylint: disable=too-few-public-methods

    quiz_id = db.Column(db.Integer, primary_key=True)

    unique_id = db.Column(

        db.String(36),

        default=lambda: str(uuid.uuid4()),

        unique=True,

        nullable=False

    )

    name = db.Column(db.String(100), nullable=False)

    description = db.Column(db.String(500))

    # Relationship to Question via junction table

    questions = db.relationship(

        'Question',

        secondary='quiz_question',

        backref='quizzes',

        cascade="all, delete"

    )
