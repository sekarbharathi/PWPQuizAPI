from app import db

class Quiz(db.Model):
    quiz_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500))

    # Relationship to Question via junction table
    questions = db.relationship('Question', secondary='quiz_question', backref='quizzes')

