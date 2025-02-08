from app import db
import sqlalchemy as sa

class Question(db.Model):
    question_id = db.Column(db.Integer, primary_key=True)
    question_statement = db.Column(db.String(500), nullable=False)
    complex_level = db.Column(db.String(20), nullable=False)

    # Adding the check constraint using sa.CheckConstraint
    __table_args__ = (
        sa.CheckConstraint(
            "complex_level IN ('easy', 'medium', 'hard')",
            name="check_complex_level"
        ),
    )

    # Relationship to Option (Multiple options per question)
    options = db.relationship('Option', backref='question', cascade="all, delete-orphan")
