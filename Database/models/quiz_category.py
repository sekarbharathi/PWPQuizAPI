from app import db

class QuizCategory(db.Model):
    __tablename__ = 'quiz_category'

    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.quiz_id'), primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), primary_key=True)
