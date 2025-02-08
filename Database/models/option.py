from app import db

class Option(db.Model):
    option_id = db.Column(db.Integer, primary_key=True)
    option_statement = db.Column(db.String(500), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.question_id'), nullable=False)


