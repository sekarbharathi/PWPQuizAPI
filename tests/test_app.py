import pytest
import sys
import os
import uuid

# Add the project root (PWPQuizAPI) to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from app import app, db, cache
from models import Category, Quiz, Question, Option, QuizQuestion, QuizCategory
from flask_jwt_extended import create_access_token

@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["CACHE_TYPE"] = "SimpleCache"  # Use in-memory caching for testing
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            cache.clear()  # Clear cache before each test
        yield client
        with app.app_context():
            db.drop_all()

def get_auth_header():
    with app.app_context():
        access_token = create_access_token(identity="admin")
    return {"Authorization": f"Bearer {access_token}"}

# Helper function to get unique_id from response
def get_unique_id(response):
    return response.json.get("unique_id")

# Login Tests
def test_login(client):
    # Test successful login
    response = client.post("/login", json={"username": "admin", "password": "admin123"})
    assert response.status_code == 200
    assert "access_token" in response.json

    # Test invalid credentials
    response = client.post("/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401

    # Test invalid JSON schema
    response = client.post("/login", json={"username": "admin"})  # Missing "password"
    assert response.status_code == 400

# Category Tests
def test_get_categories(client):
    # Test empty categories
    response = client.get("/category")
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) == 0

    # Add a category and test again
    client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    response = client.get("/category")
    assert response.status_code == 200
    assert len(response.json) == 1

def test_create_category(client):
    # Test successful creation
    response = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    assert response.status_code == 201
    assert "unique_id" in response.json
    unique_id = get_unique_id(response)

    # Test unauthorized access
    response = client.post("/category", json={"name": "Science"})
    assert response.status_code == 401

    # Test invalid JSON schema
    response = client.post("/category", json={}, headers=get_auth_header())
    assert response.status_code == 400

def test_update_category(client):
    create_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    unique_id = get_unique_id(create_resp)
   
    # Test successful update
    response = client.put(f"/category/{unique_id}", json={"name": "Math"}, headers=get_auth_header())
    assert response.status_code == 200

    # Test unauthorized access
    response = client.put(f"/category/{unique_id}", json={"name": "Math"})
    assert response.status_code == 401

    # Test invalid JSON schema
    response = client.put(f"/category/{unique_id}", json={}, headers=get_auth_header())
    assert response.status_code == 400

    # Test category not found
    response = client.put(f"/category/{str(uuid.uuid4())}", json={"name": "Math"}, headers=get_auth_header())
    assert response.status_code == 404

def test_delete_category(client):
    create_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    unique_id = get_unique_id(create_resp)
   
    # Test successful deletion
    response = client.delete(f"/category/{unique_id}", headers=get_auth_header())
    assert response.status_code == 200

    # Test unauthorized access
    response = client.delete(f"/category/{unique_id}")
    assert response.status_code == 401

    # Test category not found
    response = client.delete(f"/category/{str(uuid.uuid4())}", headers=get_auth_header())
    assert response.status_code == 404

# Quiz Tests
def test_get_quizzes(client):
    response = client.get("/quiz")
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_create_quiz(client):
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
   
    # Test successful creation
    response = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    assert response.status_code == 201
    assert "unique_id" in response.json
    quiz_unique_id = get_unique_id(response)

    # Test unauthorized access
    response = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id})
    assert response.status_code == 401

    # Test invalid JSON schema
    response = client.post("/quiz", json={}, headers=get_auth_header())
    assert response.status_code == 400

    # Test category not found
    response = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": str(uuid.uuid4())}, headers=get_auth_header())
    assert response.status_code == 404

def test_update_quiz(client):
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
   
    # Test successful update
    response = client.put(f"/quiz/{quiz_unique_id}", json={
        "name": "Updated Physics",
        "description": "Updated description",
        "category_id": cat_unique_id  # Include required field
    }, headers=get_auth_header())
    assert response.status_code == 200

    # Test unauthorized access
    response = client.put(f"/quiz/{quiz_unique_id}", json={
        "name": "Updated Physics",
        "description": "Updated description",
        "category_id": cat_unique_id
    })
    assert response.status_code == 401

    # Test invalid JSON schema
    response = client.put(f"/quiz/{quiz_unique_id}", json={}, headers=get_auth_header())
    assert response.status_code == 400

    # Test quiz not found
    response = client.put(f"/quiz/{str(uuid.uuid4())}", json={
        "name": "Updated Physics",
        "description": "Updated description",
        "category_id": cat_unique_id
    }, headers=get_auth_header())
    assert response.status_code == 404

    # Test category not found
    response = client.put(f"/quiz/{quiz_unique_id}", json={
        "name": "Updated Physics",
        "description": "Updated description",
        "category_id": str(uuid.uuid4())  # Invalid category_id
    }, headers=get_auth_header())
    assert response.status_code == 404

def test_delete_quiz(client):
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
   
    # Test successful deletion
    response = client.delete(f"/quiz/{quiz_unique_id}", headers=get_auth_header())
    assert response.status_code == 200

    # Test unauthorized access
    response = client.delete(f"/quiz/{quiz_unique_id}")
    assert response.status_code == 401

    # Test quiz not found
    response = client.delete(f"/quiz/{str(uuid.uuid4())}", headers=get_auth_header())
    assert response.status_code == 404

# Question Tests
def test_create_question(client):
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
   
    # Test successful creation
    response = client.post("/question", json={
        "question_statement": "What is gravity?",
        "complex_level": "medium",
        "quiz_id": quiz_unique_id,
        "options": [{"option_statement": "A force", "is_correct": True}]
    }, headers=get_auth_header())
    assert response.status_code == 201
    assert "unique_id" in response.json
    question_unique_id = get_unique_id(response)

    # Test unauthorized access
    response = client.post("/question", json={
        "question_statement": "What is gravity?",
        "complex_level": "medium",
        "quiz_id": quiz_unique_id,
        "options": [{"option_statement": "A force", "is_correct": True}]
    })
    assert response.status_code == 401

    # Test invalid JSON schema
    response = client.post("/question", json={}, headers=get_auth_header())
    assert response.status_code == 400

    # Test quiz not found
    response = client.post("/question", json={
        "question_statement": "What is gravity?",
        "complex_level": "medium",
        "quiz_id": str(uuid.uuid4()),
        "options": [{"option_statement": "A force", "is_correct": True}]
    }, headers=get_auth_header())
    assert response.status_code == 404

def test_update_question(client):
    # First create a question
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
    question_resp = client.post("/question", json={
        "question_statement": "What is gravity?",
        "complex_level": "medium",
        "quiz_id": quiz_unique_id,
        "options": [{"option_statement": "A force", "is_correct": True}]
    }, headers=get_auth_header())
    question_unique_id = get_unique_id(question_resp)
   
    # Test successful update
    response = client.put(f"/question/{question_unique_id}", json={
        "question_statement": "Updated question",
        "complex_level": "hard",
        "quiz_id": quiz_unique_id,
        "options": [{"option_statement": "Updated option", "is_correct": True}]
    }, headers=get_auth_header())
    assert response.status_code == 200

    # Test unauthorized access
    response = client.put(f"/question/{question_unique_id}", json={
        "question_statement": "Updated question",
        "complex_level": "hard",
        "quiz_id": quiz_unique_id,
        "options": [{"option_statement": "Updated option", "is_correct": True}]
    })
    assert response.status_code == 401

    # Test invalid JSON schema
    response = client.put(f"/question/{question_unique_id}", json={}, headers=get_auth_header())
    assert response.status_code == 400

    # Test question not found
    response = client.put(f"/question/{str(uuid.uuid4())}", json={
        "question_statement": "Updated question",
        "complex_level": "hard",
        "quiz_id": quiz_unique_id,
        "options": [{"option_statement": "Updated option", "is_correct": True}]
    }, headers=get_auth_header())
    assert response.status_code == 404

    # Test quiz not found
    response = client.put(f"/question/{question_unique_id}", json={
        "question_statement": "Updated question",
        "complex_level": "hard",
        "quiz_id": str(uuid.uuid4()),
        "options": [{"option_statement": "Updated option", "is_correct": True}]
    }, headers=get_auth_header())
    assert response.status_code == 404

def test_delete_question(client):
    # First create a question
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
    question_resp = client.post("/question", json={
        "question_statement": "What is gravity?",
        "complex_level": "medium",
        "quiz_id": quiz_unique_id,
        "options": [{"option_statement": "A force", "is_correct": True}]
    }, headers=get_auth_header())
    question_unique_id = get_unique_id(question_resp)
   
    # Test successful deletion
    response = client.delete(f"/question/{question_unique_id}", headers=get_auth_header())
    assert response.status_code == 200

    # Test unauthorized access
    response = client.delete(f"/question/{question_unique_id}")
    assert response.status_code == 401

    # Test question not found
    response = client.delete(f"/question/{str(uuid.uuid4())}", headers=get_auth_header())
    assert response.status_code == 404

def test_get_questions(client):
    # First create a question
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
    client.post("/question", json={
        "question_statement": "What is gravity?",
        "complex_level": "medium",
        "quiz_id": quiz_unique_id,
        "options": [{"option_statement": "A force", "is_correct": True}]
    }, headers=get_auth_header())
   
    # Test successful retrieval
    response = client.get("/question")
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_get_question_by_id(client):
    # First create a question
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
    question_resp = client.post("/question", json={
        "question_statement": "What is gravity?",
        "complex_level": "medium",
        "quiz_id": quiz_unique_id,
        "options": [{"option_statement": "A force", "is_correct": True}]
    }, headers=get_auth_header())
    question_unique_id = get_unique_id(question_resp)
   
    # Test successful retrieval
    response = client.get(f"/question/{question_unique_id}")
    assert response.status_code == 200
    assert "unique_id" in response.json

    # Test question not found
    response = client.get(f"/question/{str(uuid.uuid4())}")
    assert response.status_code == 404

# Filtering Endpoint Tests
def test_get_category_quiz_and_questions(client):
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
    client.post("/question", json={
        "question_statement": "What is gravity?",
        "complex_level": "medium",
        "quiz_id": quiz_unique_id,
        "options": [{"option_statement": "A force", "is_correct": True}]
    }, headers=get_auth_header())
   
    # Test successful retrieval
    response = client.get("/category/Science/quiz/Physics/all")
    assert response.status_code == 200
    assert "questions" in response.json

    # Test category not found
    response = client.get("/category/Nonexistent/quiz/Physics/all")
    assert response.status_code == 404

    # Test quiz not found
    response = client.get("/category/Science/quiz/Nonexistent/all")
    assert response.status_code == 404

def test_get_quiz_questions(client):
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
    client.post("/question", json={
        "question_statement": "What is gravity?",
        "complex_level": "medium",
        "quiz_id": quiz_unique_id,
        "options": [{"option_statement": "A force", "is_correct": True}]
    }, headers=get_auth_header())
   
    # Test successful retrieval
    response = client.get("/category/Science/quiz/Physics/questions")
    assert response.status_code == 200
    assert "questions" in response.json

    # Test category not found
    response = client.get("/category/Nonexistent/quiz/Physics/questions")
    assert response.status_code == 404

    # Test quiz not found
    response = client.get("/category/Science/quiz/Nonexistent/questions")
    assert response.status_code == 404

def test_get_quizzes_by_category(client):
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
   
    # Test successful retrieval
    response = client.get(f"/quiz/category/{cat_unique_id}")
    assert response.status_code == 200
    assert isinstance(response.json, list)

    # Test category not found
    response = client.get("/quiz/category/999")
    assert response.status_code == 404

def test_get_questions_by_quiz(client):
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
    client.post("/question", json={
        "question_statement": "What is gravity?",
        "complex_level": "medium",
        "quiz_id": quiz_unique_id,
        "options": [{"option_statement": "A force", "is_correct": True}]
    }, headers=get_auth_header())
   
    # Test successful retrieval
    response = client.get(f"/quiz/{quiz_unique_id}/questions")
    assert response.status_code == 200
    assert isinstance(response.json, list)

    # Test quiz not found
    response = client.get(f"/quiz/{str(uuid.uuid4())}/questions")
    assert response.status_code == 404

# Additional test cases
def test_cache_invalidation(client):
    # Create a category and cache the response
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    response = client.get("/category")
    assert response.status_code == 200

    # Update the category and ensure cache is invalidated
    unique_id = get_unique_id(cat_resp)
    client.put(f"/category/{unique_id}", json={"name": "Math"}, headers=get_auth_header())
    response = client.get("/category")
    assert response.status_code == 200
    assert response.json[0]["name"] == "Math"

def test_update_quiz_invalid_data(client):
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
   
    # Test invalid JSON schema
    response = client.put(f"/quiz/{quiz_unique_id}", json={"name": "Updated Physics"}, headers=get_auth_header())
    assert response.status_code == 400  # Missing required fields

def test_update_question_invalid_data(client):
    # First create a question
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
    question_resp = client.post("/question", json={
        "question_statement": "What is gravity?",
        "complex_level": "medium",
        "quiz_id": quiz_unique_id,
        "options": [{"option_statement": "A force", "is_correct": True}]
    }, headers=get_auth_header())
    question_unique_id = get_unique_id(question_resp)
   
    # Test invalid JSON schema
    response = client.put(f"/question/{question_unique_id}", json={"question_statement": "Updated question"}, headers=get_auth_header())
    assert response.status_code == 400  # Missing required fields

def test_delete_question_invalid_id(client):
    # Test deleting a non-existent question
    response = client.delete(f"/question/{str(uuid.uuid4())}", headers=get_auth_header())
    assert response.status_code == 404

def test_get_questions_by_quiz_invalid_id(client):
    # Test getting questions for a non-existent quiz
    response = client.get(f"/quiz/{str(uuid.uuid4())}/questions")
    assert response.status_code == 404

def test_get_category_quiz_and_questions_invalid_data(client):
    # Test invalid category and quiz
    response = client.get("/category/Nonexistent/quiz/Nonexistent/all")
    assert response.status_code == 404

def test_get_quiz_questions_invalid_data(client):
    # Test invalid category and quiz
    response = client.get("/category/Nonexistent/quiz/Nonexistent/questions")
    assert response.status_code == 404

def test_login_invalid_schema(client):
    # Test invalid JSON schema (missing "password")
    response = client.post("/login", json={"username": "admin"})
    assert response.status_code == 400

def test_login_invalid_credentials(client):
    # Test invalid credentials
    response = client.post("/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401

def test_create_category_invalid_schema(client):
    # Test invalid JSON schema (missing "name")
    response = client.post("/category", json={}, headers=get_auth_header())
    assert response.status_code == 400

def test_update_category_invalid_schema(client):
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    unique_id = get_unique_id(cat_resp)
   
    # Test invalid JSON schema (missing "name")
    response = client.put(f"/category/{unique_id}", json={}, headers=get_auth_header())
    assert response.status_code == 400

def test_update_category_not_found(client):
    # Test updating a non-existent category
    response = client.put(f"/category/{str(uuid.uuid4())}", json={"name": "Math"}, headers=get_auth_header())
    assert response.status_code == 404

def test_delete_category_not_found(client):
    # Test deleting a non-existent category
    response = client.delete(f"/category/{str(uuid.uuid4())}", headers=get_auth_header())
    assert response.status_code == 404

def test_create_quiz_invalid_schema(client):
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
   
    # Test invalid JSON schema (missing "name")
    response = client.post("/quiz", json={}, headers=get_auth_header())
    assert response.status_code == 400

def test_update_quiz_invalid_schema(client):
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
   
    # Test invalid JSON schema (missing "name")
    response = client.put(f"/quiz/{quiz_unique_id}", json={}, headers=get_auth_header())
    assert response.status_code == 400

def test_update_quiz_not_found(client):
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
   
    # Test updating a non-existent quiz
    response = client.put(f"/quiz/{str(uuid.uuid4())}", json={
        "name": "Updated Physics", 
        "description": "Updated description", 
        "category_id": cat_unique_id
    }, headers=get_auth_header())
    assert response.status_code == 404

def test_delete_quiz_not_found(client):
    # Test deleting a non-existent quiz
    response = client.delete(f"/quiz/{str(uuid.uuid4())}", headers=get_auth_header())
    assert response.status_code == 404

def test_create_question_invalid_schema(client):
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
   
    # Test invalid JSON schema (missing "question_statement")
    response = client.post("/question", json={}, headers=get_auth_header())
    assert response.status_code == 400

def test_update_question_invalid_schema(client):
    # First create a question
    cat_resp = client.post("/category", json={"name": "Science"}, headers=get_auth_header())
    cat_unique_id = get_unique_id(cat_resp)
    quiz_resp = client.post("/quiz", json={"name": "Physics", "description": "A physics quiz", "category_id": cat_unique_id}, headers=get_auth_header())
    quiz_unique_id = get_unique_id(quiz_resp)
    question_resp = client.post("/question", json={
        "question_statement": "What is gravity?",
        "complex_level": "medium",
        "quiz_id": quiz_unique_id,
        "options": [{"option_statement": "A force", "is_correct": True}]
    }, headers=get_auth_header())
    question_unique_id = get_unique_id(question_resp)
   
    # Test invalid JSON schema (missing "question_statement")
    response = client.put(f"/question/{question_unique_id}", json={}, headers=get_auth_header())
    assert response.status_code == 400

def test_update_question_not_found(client):
    # Test updating a non-existent question
    response = client.put(f"/question/{str(uuid.uuid4())}", json={
        "question_statement": "Updated question",
        "complex_level": "hard",
        "quiz_id": str(uuid.uuid4()),
        "options": [{"option_statement": "Updated option", "is_correct": True}]
    }, headers=get_auth_header())
    assert response.status_code == 404

def test_delete_question_not_found(client):
    # Test deleting a non-existent question
    response = client.delete(f"/question/{str(uuid.uuid4())}", headers=get_auth_header())
    assert response.status_code == 404

def test_get_questions_by_quiz_not_found(client):
    # Test getting questions for a non-existent quiz
    response = client.get(f"/quiz/{str(uuid.uuid4())}/questions")
    assert response.status_code == 404

def test_get_quizzes_by_category_not_found(client):
    # Test getting quizzes for a non-existent category
    response = client.get("/quiz/category/999")
    assert response.status_code == 404

def test_get_quiz_questions_not_found(client):
    # Test getting quiz questions for a non-existent quiz
    response = client.get(f"/quiz/{str(uuid.uuid4())}/questions")
    assert response.status_code == 404