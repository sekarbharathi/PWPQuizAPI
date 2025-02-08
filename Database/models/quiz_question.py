from app import db

class QuizQuestion(db.Model):
    __tablename__ = 'quiz_question'

    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.quiz_id'), primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('question.question_id'), primary_key=True)
