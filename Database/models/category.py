from app import db

class Category(db.Model):
    category_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # Relationship to Quiz via junction table
    quizzes = db.relationship('Quiz', secondary='quiz_category', backref='categories')

