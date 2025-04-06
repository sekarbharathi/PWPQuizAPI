import os
import sys
import pytest
import uuid
import json
from flask_jwt_extended import create_access_token
from flask import url_for

# Add the parent directory to the path to ensure imports work correctly
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + "/.."))

from app import app, db, cache
from models import Quiz, Category, Option, Question, QuizQuestion, QuizCategory

from urllib.parse import quote

# Generate test IDs
TEST_QUIZ_ID = str(uuid.uuid4())
TEST_QUESTION_ID = str(uuid.uuid4())
TEST_CATEGORY_NAME = "Test Category"
TEST_QUIZ_NAME = "Test Quiz"

@pytest.fixture(scope="function")
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:?check_same_thread=False'
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['SERVER_NAME'] = 'localhost'  # Required for url_for to work in tests
    
    with app.app_context():
        db.create_all()
        # Create test data
        test_category = Category(name=TEST_CATEGORY_NAME)
        db.session.add(test_category)
        db.session.flush()
        
        test_quiz = Quiz(name=TEST_QUIZ_NAME, description="Test Description", unique_id=TEST_QUIZ_ID)
        db.session.add(test_quiz)
        db.session.flush()
        
        quiz_category = QuizCategory(quiz_id=test_quiz.quiz_id, category_id=test_category.category_id)
        db.session.add(quiz_category)
        
        test_question = Question(question_statement="Test Question", complex_level="medium", unique_id=TEST_QUESTION_ID)
        db.session.add(test_question)
        db.session.flush()
        
        quiz_question = QuizQuestion(quiz_id=test_quiz.quiz_id, question_id=test_question.question_id)
        db.session.add(quiz_question)
        
        test_option = Option(option_statement="Test Option", is_correct=True, question_id=test_question.question_id)
        db.session.add(test_option)
        
        db.session.commit()
        
        # Clear cache for testing
        cache.clear()
        
        with app.test_client() as client:
            yield client
        
        # Rollback any pending transactions
        db.session.rollback()
        db.drop_all()

def get_admin_token():
    with app.app_context():
        return create_access_token(identity="admin")

# Authentication Tests
def test_login_success(client):
    response = client.post('/login', json={
        'username': 'admin',
        'password': 'admin123'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_login_failure(client):
    response = client.post('/login', json={
        'username': 'wrong',
        'password': 'wrong'
    })
    assert response.status_code == 401
    assert response.json['msg'] == 'Invalid credentials'

def test_login_invalid_schema(client):
    response = client.post('/login', json={
        'username': 'admin'  # Missing password
    })
    assert response.status_code == 400
    assert "Invalid request" in response.json['msg']

# Category Tests
def test_get_categories(client):
    response = client.get('/category')
    assert response.status_code == 200
    assert 'categories' in response.json
    assert any(cat['name'] == TEST_CATEGORY_NAME for cat in response.json['categories'])
    assert '_links' in response.json

def test_create_category(client):
    token = get_admin_token()
    response = client.post('/category', 
        json={'name': 'New Category'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    assert response.json['msg'] == 'Category created'
    assert response.json['name'] == 'New Category'
    assert '_links' in response.json

def test_create_category_unauthorized(client):
    response = client.post('/category', json={'name': 'New Category'})
    assert response.status_code == 401

def test_create_category_duplicate(client):
    token = get_admin_token()
    response = client.post('/category', 
        json={'name': TEST_CATEGORY_NAME},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert "Category already exists" in response.json['msg']

def test_create_category_empty_name(client):
    token = get_admin_token()
    response = client.post('/category', 
        json={'name': '   '},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400

def test_get_category_detail(client):
    response = client.get(f'/category/{TEST_CATEGORY_NAME}')
    assert response.status_code == 200
    assert response.json['name'] == TEST_CATEGORY_NAME
    assert '_links' in response.json

def test_update_category(client):
    token = get_admin_token()
    client.preserve_context = False
    response = client.put(f'/category/{TEST_CATEGORY_NAME}', 
        json={'name': 'Updated Category'},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    assert response.status_code == 200
    assert response.json['msg'] == 'Category updated'
    assert response.json['new_name'] == 'Updated Category'

def test_delete_category(client):
    # First create a category that can be deleted (not the one with quizzes)
    token = get_admin_token()
    client.preserve_context = False
    client.post('/category', 
        json={'name': 'To Delete'},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    response = client.delete(f'/category/To Delete', 
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    assert response.json['msg'] == 'Category deleted'

def test_delete_category_in_use(client):
    token = get_admin_token()
    client.preserve_context = False
    response = client.delete(f'/category/{TEST_CATEGORY_NAME}', 
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert "Cannot delete category in use by quizzes" in response.json['msg']

# Quiz Tests
def test_get_quizzes(client):
    response = client.get('/quiz')
    assert response.status_code == 200
    assert 'quizzes' in response.json
    assert any(quiz['unique_id'] == TEST_QUIZ_ID for quiz in response.json['quizzes'])
    assert '_links' in response.json

def test_create_quiz(client):
    token = get_admin_token()
    response = client.post('/quiz', 
        json={
            'name': 'New Quiz',
            'description': 'New Description',
            'category_name': TEST_CATEGORY_NAME
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    assert 'unique_id' in response.json
    assert '_links' in response.json

def test_create_quiz_invalid_category(client):
    token = get_admin_token()
    response = client.post('/quiz', 
        json={
            'name': 'New Quiz',
            'description': 'New Description',
            'category_name': 'Non-existent Category'
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 404
    assert "Category not found" in response.json['msg']

def test_get_quiz_detail(client):
    response = client.get(f'/quiz/{TEST_QUIZ_ID}')
    assert response.status_code == 200
    assert response.json['unique_id'] == TEST_QUIZ_ID
    assert response.json['name'] == TEST_QUIZ_NAME
    assert '_links' in response.json

def test_update_quiz(client):
    token = get_admin_token()
    client.preserve_context = False
    response = client.put(f'/quiz/{TEST_QUIZ_ID}', 
        json={
            'name': 'Updated Quiz',
            'description': 'Updated Description',
            'category_name': TEST_CATEGORY_NAME
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    assert response.json['msg'] == 'Quiz updated'

def test_delete_quiz(client):
    # First create a quiz that can be deleted
    token = get_admin_token()
    client.preserve_context = False
    create_resp = client.post('/quiz', 
        json={
            'name': 'Quiz To Delete',
            'description': 'To be deleted',
            'category_name': TEST_CATEGORY_NAME
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    quiz_id = create_resp.json['unique_id']
    
    response = client.delete(f'/quiz/{quiz_id}', 
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    assert response.json['msg'] == 'Quiz deleted'

# Question Tests
def test_get_questions(client):
    response = client.get('/question')
    assert response.status_code == 200
    assert 'questions' in response.json
    assert any(q['unique_id'] == TEST_QUESTION_ID for q in response.json['questions'])
    assert '_links' in response.json

def test_create_question(client):
    token = get_admin_token()
    response = client.post('/question', 
        json={
            'question_statement': 'New Question',
            'complex_level': 'easy',
            'quiz_unique_id': TEST_QUIZ_ID,
            'options': [
                {'option_statement': 'Option A', 'is_correct': True},
                {'option_statement': 'Option B', 'is_correct': False}
            ]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    assert 'unique_id' in response.json
    assert '_links' in response.json

def test_get_question_detail(client):
    response = client.get(f'/question/{TEST_QUESTION_ID}')
    assert response.status_code == 200
    assert response.json['unique_id'] == TEST_QUESTION_ID
    assert response.json['question_statement'] == 'Test Question'
    assert '_links' in response.json

def test_update_question(client):
    token = get_admin_token()
    client.preserve_context = False
    response = client.put(f'/question/{TEST_QUESTION_ID}', 
        json={
            'question_statement': 'Updated Question',
            'complex_level': 'hard',
            'quiz_unique_id': TEST_QUIZ_ID,
            'options': [
                {'option_statement': 'Updated Option', 'is_correct': True}
            ]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    assert response.json['msg'] == 'Question updated'

def test_delete_question(client):
    # First create a question that can be deleted
    token = get_admin_token()
    client.preserve_context = False
    create_resp = client.post('/question', 
        json={
            'question_statement': 'Question To Delete',
            'complex_level': 'easy',
            'quiz_unique_id': TEST_QUIZ_ID,
            'options': [
                {'option_statement': 'Option A', 'is_correct': True}
            ]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    question_id = create_resp.json['unique_id']
    
    response = client.delete(f'/question/{question_id}', 
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    assert response.json['msg'] == 'Question and related records deleted'

# Quiz by Category Tests
def test_get_quizzes_by_category(client):
    response = client.get(f'/category/{TEST_CATEGORY_NAME}/quizzes')
    assert response.status_code == 200
    assert 'quizzes' in response.json
    assert any(q['unique_id'] == TEST_QUIZ_ID for q in response.json['quizzes'])
    assert '_links' in response.json

# Questions by Quiz Tests
def test_get_questions_by_quiz(client):
    response = client.get(f'/quiz/{TEST_QUIZ_ID}/questions')
    assert response.status_code == 200
    assert 'questions' in response.json
    assert any(q['unique_id'] == TEST_QUESTION_ID for q in response.json['questions'])
    assert '_links' in response.json

# Category Quiz Questions Tests
def test_get_category_quiz_questions(client):
    response = client.get(f'/category/{TEST_CATEGORY_NAME}/quiz/{TEST_QUIZ_NAME}/all')
    assert response.status_code == 200
    assert 'questions' in response.json
    assert response.json['quiz'] == TEST_QUIZ_NAME
    assert response.json['category'] == TEST_CATEGORY_NAME

# Filtered Quiz Questions Tests
def test_get_filtered_quiz_questions(client):
    response = client.get(f'/category/{TEST_CATEGORY_NAME}/quiz/{TEST_QUIZ_NAME}/questions?question_count=1&complex_level=easy')
    assert response.status_code == 200
    assert 'questions' in response.json
    assert '_links' in response.json

def test_create_question_for_quiz(client):
    token = get_admin_token()
    response = client.post(f'/category/{TEST_CATEGORY_NAME}/quiz/{TEST_QUIZ_NAME}/questions', 
        json={
            'question_statement': 'New Question for Quiz',
            'complex_level': 'easy',
            'options': [
                {'option_statement': 'Option A', 'is_correct': True},
                {'option_statement': 'Option B', 'is_correct': False}
            ]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    assert 'question_id' in response.json
    assert '_links' in response.json

# Content Type Validation
def test_invalid_content_type(client):
    response = client.post('/login', data="not json")
    assert response.status_code == 400
    assert "Missing JSON in request" in response.json['msg']

# Cache Tests
def test_cache_invalidation(client):
    # Get initial categories
    response1 = client.get('/category')
    initial_count = len(response1.json['categories'])
    
    # Add a new category
    token = get_admin_token()
    new_cat_name = f"Cache Test {uuid.uuid4()}"
    client.post('/category',
        json={'name': new_cat_name},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    # Get categories again - should include the new one
    response2 = client.get('/category')
    new_count = len(response2.json['categories'])
    
    assert new_count > initial_count
    assert any(cat['name'] == new_cat_name for cat in response2.json['categories'])

# Additional Validation Tests
def test_question_without_correct_option(client):
    token = get_admin_token()
    response = client.post('/question',
        json={
            'question_statement': 'No correct option',
            'complex_level': 'easy',
            'quiz_unique_id': TEST_QUIZ_ID,
            'options': [
                {'option_statement': 'Option 1', 'is_correct': False},
                {'option_statement': 'Option 2', 'is_correct': False}
            ]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert "at least one option must be marked as correct" in response.json['msg'].lower()

def test_question_with_multiple_correct_options(client):
    token = get_admin_token()
    response = client.post('/question',
        json={
            'question_statement': 'Multi-correct',
            'complex_level': 'easy',
            'quiz_unique_id': TEST_QUIZ_ID,
            'options': [
                {'option_statement': 'A', 'is_correct': True},
                {'option_statement': 'B', 'is_correct': True},
                {'option_statement': 'C', 'is_correct': False}
            ]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    assert 'unique_id' in response.json

def test_empty_options_array(client):
    token = get_admin_token()
    response = client.post('/question',
        json={
            'question_statement': 'Empty options',
            'complex_level': 'easy',
            'quiz_unique_id': TEST_QUIZ_ID,
            'options': []
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400  # Should probably be 400, not 201

def test_invalid_option_structure(client):
    token = get_admin_token()
    response = client.post('/question',
        json={
            'question_statement': 'Invalid option',
            'complex_level': 'easy',
            'quiz_unique_id': TEST_QUIZ_ID,
            'options': [
                {'invalid_field': 'value'}  # Missing required option_statement
            ]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert "Invalid request" in response.json['msg']

def test_invalid_complexity_level(client):
    token = get_admin_token()
    response = client.post('/question',
        json={
            'question_statement': 'Invalid complexity',
            'complex_level': 'invalid',
            'quiz_unique_id': TEST_QUIZ_ID,
            'options': [{'option_statement': 'A', 'is_correct': True}]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert "Invalid complexity level" in response.json['msg']

# Test 404 scenarios
def test_nonexistent_quiz_detail(client):
    with pytest.raises(ValueError) as excinfo:
        client.get('/quiz/00000000-0000-0000-0000-000000000000')
    assert "not found" in str(excinfo.value).lower()


def test_nonexistent_question_detail(client):
    with pytest.raises(ValueError) as excinfo:
        client.get('/question/nonexistent-id')
    assert "not found" in str(excinfo.value).lower()



def test_nonexistent_category_detail(client):
    with pytest.raises(ValueError) as excinfo:
        client.get('/category/nonexistent-category')
    assert "not found" in str(excinfo.value).lower()

# Test unauthorized access to protected endpoints
def test_unauthorized_category_creation(client):
    response = client.post('/category', json={'name': 'New Category'})
    assert response.status_code == 401

def test_unauthorized_quiz_creation(client):
    response = client.post('/quiz', json={'name': 'New Quiz', 'category_name': TEST_CATEGORY_NAME})
    assert response.status_code == 401

def test_unauthorized_question_creation(client):
    response = client.post('/question', json={'question_statement': 'New Question', 'quiz_unique_id': TEST_QUIZ_ID})
    assert response.status_code == 401
    
    
def test_category_converter(client):
    """Test the CategoryConverter's to_python and to_url methods."""
    with client.application.app_context():
        # Test valid conversion
        converter = client.application.url_map.converters['category']({})
        category = converter.to_python(TEST_CATEGORY_NAME)
        assert category.name == TEST_CATEGORY_NAME
        
        # Test to_url with Category object
        url_value = converter.to_url(category)
        assert url_value == TEST_CATEGORY_NAME
        
        # Test to_url with string
        url_value = converter.to_url("Test String")
        assert url_value == "Test String"
        
        # Test non-existent category
        with pytest.raises(ValueError) as excinfo:
            converter.to_python("Non-existent Category")
        assert "not found" in str(excinfo.value).lower()

def test_quiz_converter(client):
    """Test the QuizConverter's to_python and to_url methods."""
    with client.application.app_context():
        # Test valid conversion
        converter = client.application.url_map.converters['quiz']({})
        quiz = converter.to_python(TEST_QUIZ_ID)
        assert quiz.unique_id == TEST_QUIZ_ID
        
        # Test to_url with Quiz object
        url_value = converter.to_url(quiz)
        assert url_value == TEST_QUIZ_ID
        
        # Test to_url with string
        url_value = converter.to_url("test-string")
        assert url_value == "test-string"
        
        # Test invalid UUID format
        with pytest.raises(ValueError) as excinfo:
            converter.to_python("not-a-uuid")
        assert "Invalid quiz ID format" in str(excinfo.value)
        
        # Test valid UUID format but non-existent quiz
        non_existent_id = str(uuid.uuid4())
        with pytest.raises(ValueError) as excinfo:
            converter.to_python(non_existent_id)
        assert "not found" in str(excinfo.value).lower()

def test_question_converter(client):
    """Test the QuestionConverter's to_python and to_url methods."""
    with client.application.app_context():
        # Test valid conversion
        converter = client.application.url_map.converters['question']({})
        question = converter.to_python(TEST_QUESTION_ID)
        assert question.unique_id == TEST_QUESTION_ID
        
        # Test to_url with Question object
        url_value = converter.to_url(question)
        assert url_value == TEST_QUESTION_ID
        
        # Test to_url with string
        url_value = converter.to_url("test-string")
        assert url_value == "test-string"

def test_complexity_converter(client):
    """Test the ComplexityConverter's to_python method."""
    with client.application.app_context():
        converter = client.application.url_map.converters['complexity']({})
        
        # Test valid values
        assert converter.to_python("easy") == "easy"
        assert converter.to_python("MEDIUM") == "medium"
        assert converter.to_python("Hard") == "hard"
        
        # Test invalid value
        with pytest.raises(ValueError) as excinfo:
            converter.to_python("invalid")
        assert "Invalid complexity level" in str(excinfo.value)


# Additional validation tests
def test_validate_json_function(client):
    """Test the validate_json function directly."""
    from app import validate_json, login_schema
    
    # Valid data
    valid_data = {"username": "test", "password": "test123"}
    is_valid, error = validate_json(valid_data, login_schema)
    assert is_valid is True
    assert error is None
    
    # Invalid data (missing required field)
    invalid_data = {"username": "test"}  # Missing password
    is_valid, error = validate_json(invalid_data, login_schema)
    assert is_valid is False
    assert error is not None
    assert "password" in error.lower()
    
    # Invalid data (wrong type)
    invalid_data = {"username": 123, "password": "test123"}  # Username should be string
    is_valid, error = validate_json(invalid_data, login_schema)
    assert is_valid is False
    assert error is not None

def test_add_hypermedia_links_function(client):
    """Test the add_hypermedia_links function directly."""
    from app import add_hypermedia_links
    
    with client.application.app_context():
        # Test adding links to a resource without ID
        data = {"name": "test"}
        result = add_hypermedia_links(data, "category")
        assert "_links" in result
        assert "self" in result["_links"]
        
        # Test adding links to a resource with ID
        data = {"name": "test"}
        result = add_hypermedia_links(data, "category", TEST_CATEGORY_NAME)
        assert "_links" in result
        assert "self" in result["_links"]
        assert "collection" in result["_links"]
        
        # Test quiz resource
        data = {"name": "test"}
        result = add_hypermedia_links(data, "quiz", TEST_QUIZ_ID)
        assert "_links" in result
        assert "questions" in result["_links"]
        
        # Test non-dict input (should remain unchanged)
        data = ["item1", "item2"]
        result = add_hypermedia_links(data, "category")
        assert result == data

# Error handling tests
def test_value_error_handler(client):
    """Test the custom ValueError handler."""
    # The handler is tested indirectly in other tests, but we can test it directly
    # by causing a ValueError in the application context
    with client.application.app_context():
        from app import handle_value_error
        response, status_code = handle_value_error(ValueError("Test error message"))
        assert status_code == 404
        assert response.json["msg"] == "Test error message"

def test_check_content_type(client):
    """Test the before_request function that checks content type."""
    # Test with non-JSON content type on POST request
    response = client.post('/login', data="not json", content_type="text/plain")
    assert response.status_code == 400
    assert "Missing JSON in request" in response.json["msg"]
    
    # Test with JSON content type (should proceed normally)
    response = client.post('/login', json={"username": "wrong", "password": "wrong"})
    assert response.status_code == 401  # Should get authentication error, not content type error

# Additional edge cases in resource endpoints
def test_create_category_with_whitespace(client):
    """Test creating a category with a name that's just whitespace."""
    token = get_admin_token()
    response = client.post('/category', 
        json={'name': '    '},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert "Category name cannot be empty" in response.json["msg"]

def test_create_question_with_invalid_quiz_id(client):
    """Test creating a question with a non-existent quiz ID."""
    token = get_admin_token()
    non_existent_id = str(uuid.uuid4())
    response = client.post('/question', 
        json={
            'question_statement': 'Test Question',
            'complex_level': 'easy',
            'quiz_unique_id': non_existent_id,
            'options': [{'option_statement': 'Option A', 'is_correct': True}]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 404
    assert "Quiz not found" in response.json["msg"]

def test_filtered_quiz_questions_invalid_complexity(client):
    """Test the filtered quiz questions endpoint with an invalid complexity level."""
    response = client.get(f'/category/{TEST_CATEGORY_NAME}/quiz/{TEST_QUIZ_NAME}/questions?complex_level=invalid')
    assert response.status_code == 400
    assert "Invalid complexity level" in response.json["msg"]

def test_filtered_quiz_questions_non_existent_quiz(client):
    """Test the filtered quiz questions endpoint with a non-existent quiz."""
    response = client.get(f'/category/{TEST_CATEGORY_NAME}/quiz/non-existent-quiz/questions')
    assert response.status_code == 404
    assert "Quiz not found" in response.json["msg"]

def test_filtered_quiz_questions_non_existent_category(client):
    """Test the filtered quiz questions endpoint with a non-existent category."""
    response = client.get(f'/category/non-existent-category/quiz/{TEST_QUIZ_NAME}/questions')
    assert response.status_code == 404
    assert "Category not found" in response.json["msg"]

def test_filtered_quiz_questions_quiz_not_in_category(client):
    """Test the filtered quiz questions endpoint with a quiz not belonging to the category."""
    # First create a new category and quiz
    token = get_admin_token()
    client.post('/category', 
        json={'name': 'Another Category'},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    client.post('/quiz', 
        json={
            'name': 'Another Quiz',
            'description': 'Another Description',
            'category_name': 'Another Category'
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    
    # Now try to access the quiz with a different category
    response = client.get(f'/category/Another Category/quiz/{TEST_QUIZ_NAME}/questions')
    assert response.status_code == 404
    assert "Quiz not found in this category" in response.json["msg"]

def test_update_question_with_no_correct_option(client):
    """Test updating a question to have no correct options."""
    token = get_admin_token()
    response = client.put(f'/question/{TEST_QUESTION_ID}', 
        json={
            'question_statement': 'Updated Question',
            'complex_level': 'easy',
            'quiz_unique_id': TEST_QUIZ_ID,
            'options': [
                {'option_statement': 'Option A', 'is_correct': False},
                {'option_statement': 'Option B', 'is_correct': False}
            ]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert "at least one option must be marked as correct" in response.json["msg"].lower()

def test_create_filtered_question_with_no_correct_option(client):
    """Test creating a filtered question with no correct options."""
    token = get_admin_token()
    response = client.post(f'/category/{TEST_CATEGORY_NAME}/quiz/{TEST_QUIZ_NAME}/questions', 
        json={
            'question_statement': 'No Correct Option',
            'complex_level': 'easy',
            'options': [
                {'option_statement': 'Option A', 'is_correct': False},
                {'option_statement': 'Option B', 'is_correct': False}
            ]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert "at least one option must be marked as correct" in response.json["msg"].lower()

# Additional tests for CategoryQuizQuestionsResource and FilteredQuizQuestionsResource
def test_category_quiz_questions_nonexistent_quiz(client):
    """Test CategoryQuizQuestionsResource with a non-existent quiz."""
    response = client.get(f'/category/{TEST_CATEGORY_NAME}/quiz/non-existent-quiz/all')
    assert response.status_code == 404
    assert "Quiz not found" in response.json["msg"]

def test_category_quiz_questions_nonexistent_category(client):
    """Test CategoryQuizQuestionsResource with a non-existent category."""
    response = client.get(f'/category/non-existent-category/quiz/{TEST_QUIZ_NAME}/all')
    assert response.status_code == 404
    assert "Category not found" in response.json["msg"]
    
def test_category_quiz_questions_wrong_category(client):
    """Test CategoryQuizQuestionsResource with a quiz not in the specified category."""
    # First create a new category
    token = get_admin_token()
    client.post('/category', 
        json={'name': 'Wrong Category'},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    # Now try to access a quiz with a category it doesn't belong to
    response = client.get(f'/category/Wrong Category/quiz/{TEST_QUIZ_NAME}/all')
    assert response.status_code == 404
    assert "Quiz not found in this category" in response.json["msg"]

def test_filtered_quiz_questions_post_invalid_schema(client):
    """Test FilteredQuizQuestionsResource POST with invalid request schema."""
    token = get_admin_token()
    response = client.post(f'/category/{TEST_CATEGORY_NAME}/quiz/{TEST_QUIZ_NAME}/questions', 
        json={
            # Missing required fields
            'complex_level': 'easy',
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert "Invalid request" in response.json["msg"]

def test_filtered_quiz_questions_post_nonexistent_category(client):
    """Test FilteredQuizQuestionsResource POST with a non-existent category."""
    token = get_admin_token()
    response = client.post(f'/category/non-existent-category/quiz/{TEST_QUIZ_NAME}/questions', 
        json={
            'question_statement': 'Test Question',
            'complex_level': 'easy',
            'options': [{'option_statement': 'Option A', 'is_correct': True}]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 404
    assert "Category not found" in response.json["msg"]

def test_filtered_quiz_questions_post_nonexistent_quiz(client):
    """Test FilteredQuizQuestionsResource POST with a non-existent quiz."""
    token = get_admin_token()
    response = client.post(f'/category/{TEST_CATEGORY_NAME}/quiz/non-existent-quiz/questions', 
        json={
            'question_statement': 'Test Question',
            'complex_level': 'easy',
            'options': [{'option_statement': 'Option A', 'is_correct': True}]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 404
    assert "Quiz not found" in response.json["msg"]

def test_filtered_quiz_questions_post_unauthorized(client):
    """Test FilteredQuizQuestionsResource POST without authorization."""
    response = client.post(f'/category/{TEST_CATEGORY_NAME}/quiz/{TEST_QUIZ_NAME}/questions', 
        json={
            'question_statement': 'Test Question',
            'complex_level': 'easy',
            'options': [{'option_statement': 'Option A', 'is_correct': True}]
        }
    )
    assert response.status_code == 401

# Cache-related tests
def test_quiz_cache_invalidation(client):
    """Test that quiz cache is invalidated when a new quiz is created."""
    # Get initial quizzes
    response1 = client.get('/quiz')
    initial_count = len(response1.json['quizzes'])
    
    # Add a new quiz
    token = get_admin_token()
    client.post('/quiz', 
        json={
            'name': f'Cache Test Quiz {uuid.uuid4()}',
            'description': 'Test Description',
            'category_name': TEST_CATEGORY_NAME
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    
    # Get quizzes again - should include the new one
    response2 = client.get('/quiz')
    new_count = len(response2.json['quizzes'])
    
    assert new_count > initial_count

# Integration tests
def test_full_quiz_workflow(client):
    """Test the full workflow of creating and managing a quiz."""
    client.preserve_context = False
    token = get_admin_token()
    
    # 1. Create a new category
    category_name = f"Integration Test Category {uuid.uuid4()}"
    cat_response = client.post('/category', 
        json={'name': category_name},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert cat_response.status_code == 201
    
    # 2. Create a new quiz in the category
    quiz_name = f"Integration Test Quiz {uuid.uuid4()}"
    quiz_response = client.post('/quiz', 
        json={
            'name': quiz_name,
            'description': 'Integration Test Description',
            'category_name': category_name
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert quiz_response.status_code == 201
    quiz_id = quiz_response.json['unique_id']
    
    # 3. Add a question to the quiz
    question_response = client.post('/question', 
        json={
            'question_statement': 'Integration Test Question',
            'complex_level': 'medium',
            'quiz_unique_id': quiz_id,
            'options': [
                {'option_statement': 'Option A', 'is_correct': True},
                {'option_statement': 'Option B', 'is_correct': False}
            ]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert question_response.status_code == 201
    question_id = question_response.json['unique_id']
    
    # 4. Get the quiz details
    quiz_details_response = client.get(f'/quiz/{quiz_id}')
    assert quiz_details_response.status_code == 200
    assert quiz_details_response.json['name'] == quiz_name
    assert quiz_details_response.json['category'] == category_name
    
    # 5. Get questions for the quiz
    questions_response = client.get(f'/quiz/{quiz_id}/questions')
    assert questions_response.status_code == 200
    assert len(questions_response.json['questions']) == 1
    assert questions_response.json['questions'][0]['unique_id'] == question_id
    
    # 6. Get filtered questions
    filtered_response = client.get(f'/category/{category_name}/quiz/{quiz_name}/questions?complex_level=medium')
    assert filtered_response.status_code == 200
    assert len(filtered_response.json['questions']) == 1
    
    # 7. Update the question
    update_q_response = client.put(f'/question/{question_id}', 
        json={
            'question_statement': 'Updated Integration Test Question',
            'complex_level': 'hard',
            'quiz_unique_id': quiz_id,
            'options': [
                {'option_statement': 'Updated Option A', 'is_correct': True},
                {'option_statement': 'Updated Option B', 'is_correct': False}
            ]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert update_q_response.status_code == 200
    
    # 8. Get the updated question
    question_detail_response = client.get(f'/question/{question_id}')
    assert question_detail_response.status_code == 200
    assert question_detail_response.json['question_statement'] == 'Updated Integration Test Question'
    assert question_detail_response.json['complex_level'] == 'hard'
    
    # 9. First, delete the question
    delete_q_response = client.delete(f'/question/{question_id}', 
        headers={'Authorization': f'Bearer {token}'}
    )
    assert delete_q_response.status_code == 200
    
    # 10. Then, delete the quiz
    delete_quiz_response = client.delete(f'/quiz/{quiz_id}', 
        headers={'Authorization': f'Bearer {token}'}
    )
    assert delete_quiz_response.status_code == 200
    
    # 11. Finally delete the category
    delete_cat_response = client.delete(f'/category/{category_name}', 
        headers={'Authorization': f'Bearer {token}'}
    )
    assert delete_cat_response.status_code == 200


def test_quiz_category_relationship_management(client):
    """Test that changing a quiz's category works correctly."""
    token = get_admin_token()
    client.preserve_context = False
    # 1. Create two categories
    cat1_name = f"Category One {uuid.uuid4()}"
    cat2_name = f"Category Two {uuid.uuid4()}"
    
    client.post('/category', 
        json={'name': cat1_name},
        headers={'Authorization': f'Bearer {token}'}
    )
    client.post('/category', 
        json={'name': cat2_name},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    # 2. Create a quiz in category 1
    quiz_name = f"Movable Quiz {uuid.uuid4()}"
    quiz_response = client.post('/quiz', 
        json={
            'name': quiz_name,
            'description': 'Test Description',
            'category_name': cat1_name
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    quiz_id = quiz_response.json['unique_id']
    
    # 3. Verify quiz is in category 1
    cat1_quizzes = client.get(f'/category/{cat1_name}/quizzes')
    assert any(quiz['unique_id'] == quiz_id for quiz in cat1_quizzes.json['quizzes'])
    
    cat2_quizzes = client.get(f'/category/{cat2_name}/quizzes')
    assert not any(quiz['unique_id'] == quiz_id for quiz in cat2_quizzes.json['quizzes'])
    
    # 4. Move quiz to category 2
    client.put(f'/quiz/{quiz_id}', 
        json={
            'name': quiz_name,
            'description': 'Test Description',
            'category_name': cat2_name
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    
    # 5. Verify quiz is now in category 2
    cat1_quizzes = client.get(f'/category/{cat1_name}/quizzes')
    assert not any(quiz['unique_id'] == quiz_id for quiz in cat1_quizzes.json['quizzes'])
    
    cat2_quizzes = client.get(f'/category/{cat2_name}/quizzes')
    assert any(quiz['unique_id'] == quiz_id for quiz in cat2_quizzes.json['quizzes'])
    
    # 6. Clean up in the correct order: first delete the quiz, then the categories
    client.delete(f'/quiz/{quiz_id}', headers={'Authorization': f'Bearer {token}'})
    client.delete(f'/category/{cat1_name}', headers={'Authorization': f'Bearer {token}'})
    client.delete(f'/category/{cat2_name}', headers={'Authorization': f'Bearer {token}'})

# Advanced validation tests
def test_login_with_invalid_json(client):
    """Test login with malformed JSON."""
    response = client.post('/login', 
        data='{invalid json',
        content_type='application/json'
    )
    assert response.status_code == 400
    # The error message might be "Missing JSON" or something similar
    # Just check for the status code
    assert response.status_code == 400


def test_create_category_case_insensitive_check(client):
    """Test that category name check is case-insensitive."""
    token = get_admin_token()
    client.preserve_context = False
    # Use a unique category name
    category_name = f"Case Test Category {uuid.uuid4()}"
    
    # Create a category
    client.post('/category', 
        json={'name': category_name},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    # Try to create it again with different case
    response = client.post('/category', 
        json={'name': category_name.upper()},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert "Category already exists" in response.json["msg"]
    
    # Clean up
    client.delete(f'/category/{category_name}', 
        headers={'Authorization': f'Bearer {token}'})


def test_update_category_to_existing_name(client):
    """Test updating a category to a name that already exists."""
    token = get_admin_token()
    client.preserve_context = False
    # Use unique category names
    original_name = f"Original Category {uuid.uuid4()}"
    target_name = f"Target Category {uuid.uuid4()}"
    
    # Create two categories
    client.post('/category', 
        json={'name': original_name},
        headers={'Authorization': f'Bearer {token}'}
    )
    client.post('/category', 
        json={'name': target_name},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    # Try to update the first to have the same name as the second
    response = client.put(f'/category/{original_name}', 
        json={'name': target_name},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 400
    assert "Category name already exists" in response.json["msg"]
    
    # Clean up
    client.delete(f'/category/{original_name}', 
        headers={'Authorization': f'Bearer {token}'}
    )
    
    client.delete(f'/category/{target_name}', 
        headers={'Authorization': f'Bearer {token}'}
    )


def test_update_category_to_same_name_different_case(client):
    """Test updating a category to the same name but with different case."""
    token = get_admin_token()
    client.preserve_context = False
    # Create a category
    client.post('/category', 
        json={'name': 'Case Update Category'},
        headers={'Authorization': f'Bearer {token}'}
    )
    
    # Update to the same name but different case
    response = client.put('/category/Case Update Category', 
        json={'name': 'CASE UPDATE CATEGORY'},
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 200
    assert response.json["new_name"] == 'CASE UPDATE CATEGORY'
    
    # Clean up
    client.delete(f'/category/CASE UPDATE CATEGORY', 
        headers={'Authorization': f'Bearer {token}'}
    )

# Test QuizCategory and QuizQuestion relationships
def test_quiz_question_associations(client):
    """Test the association between quizzes and questions."""
    token = get_admin_token()
    client.preserve_context = False
    # Create a new quiz
    quiz_response = client.post('/quiz', 
        json={
            'name': f'Association Quiz {uuid.uuid4()}',
            'description': 'Test Description',
            'category_name': TEST_CATEGORY_NAME
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    quiz_id = quiz_response.json['unique_id']
    
    # Create questions for this quiz
    for i in range(3):
        client.post('/question', 
            json={
                'question_statement': f'Test Question {i}',
                'complex_level': 'medium',
                'quiz_unique_id': quiz_id,
                'options': [
                    {'option_statement': 'Option A', 'is_correct': True},
                    {'option_statement': 'Option B', 'is_correct': False}
                ]
            },
            headers={'Authorization': f'Bearer {token}'}
        )
    
    # Verify quiz has 3 questions
    questions_response = client.get(f'/quiz/{quiz_id}/questions')
    assert len(questions_response.json['questions']) == 3
    
    # Delete the quiz
    client.delete(f'/quiz/{quiz_id}', 
        headers={'Authorization': f'Bearer {token}'}
    )
    
    # Verify questions were also deleted (or orphaned)
    # The unique IDs would no longer be valid
    question_ids = [q['unique_id'] for q in questions_response.json['questions']]
    for q_id in question_ids:
        with pytest.raises(ValueError) as excinfo:
            client.get(f'/question/{q_id}')
        assert "not found" in str(excinfo.value).lower()

def test_multiple_quizzes_sharing_question(client):
    """Test that questions can be shared between multiple quizzes."""
    token = get_admin_token()
    client.preserve_context = False
    # Create two quizzes
    quiz1_response = client.post('/quiz', 
        json={
            'name': f'Shared Quiz 1 {uuid.uuid4()}',
            'description': 'Test Description',
            'category_name': TEST_CATEGORY_NAME
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    quiz1_id = quiz1_response.json['unique_id']
    
    quiz2_response = client.post('/quiz', 
        json={
            'name': f'Shared Quiz 2 {uuid.uuid4()}',
            'description': 'Test Description',
            'category_name': TEST_CATEGORY_NAME
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    quiz2_id = quiz2_response.json['unique_id']
    
    # Create a question for quiz1
    question_response = client.post('/question', 
        json={
            'question_statement': 'Shared Question',
            'complex_level': 'medium',
            'quiz_unique_id': quiz1_id,
            'options': [
                {'option_statement': 'Option A', 'is_correct': True},
                {'option_statement': 'Option B', 'is_correct': False}
            ]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    question_id = question_response.json['unique_id']
    
    # Ensure question appears in quiz1
    questions1 = client.get(f'/quiz/{quiz1_id}/questions')
    assert any(q['unique_id'] == question_id for q in questions1.json['questions'])
    
    # Update question to also belong to quiz2
    client.put(f'/question/{question_id}', 
        json={
            'question_statement': 'Shared Question',
            'complex_level': 'medium',
            'quiz_unique_id': quiz2_id,
            'options': [
                {'option_statement': 'Option A', 'is_correct': True},
                {'option_statement': 'Option B', 'is_correct': False}
            ]
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    
    # Verify question appears in quiz2 and not in quiz1
    questions1 = client.get(f'/quiz/{quiz1_id}/questions')
    assert not any(q['unique_id'] == question_id for q in questions1.json['questions'])
    
    questions2 = client.get(f'/quiz/{quiz2_id}/questions')
    assert any(q['unique_id'] == question_id for q in questions2.json['questions'])
    
    # Clean up
    client.delete(f'/quiz/{quiz1_id}', headers={'Authorization': f'Bearer {token}'})
    client.delete(f'/quiz/{quiz2_id}', headers={'Authorization': f'Bearer {token}'})

def test_hypermedia_links_navigation(client):
    """Test that hypermedia links can be navigated correctly."""
    # Get categories
    cat_response = client.get('/category')
    
    # Extract the self link of the first category
    first_cat_link = cat_response.json['categories'][0]['_links']['self']
    assert '/category/' in first_cat_link
    
    # Follow the link
    category_detail_response = client.get(first_cat_link.replace('http://localhost', ''))
    assert category_detail_response.status_code == 200
    
    # Extract the quizzes link
    quizzes_link = category_detail_response.json['_links']['quizzes']
    assert '/quizzes' in quizzes_link
    
    # Follow the link
    quizzes_response = client.get(quizzes_link.replace('http://localhost', ''))
    assert quizzes_response.status_code == 200
def test_options_request_handling(client):
    """Test that OPTIONS requests are handled correctly."""
    response = client.options('/category')
    assert response.status_code == 200
    assert 'Allow' in response.headers
    
    response = client.options('/login')
    assert response.status_code == 200
    assert 'Allow' in response.headers

def test_create_quiz_without_optional_description(client):
    """Test creating a quiz without providing the optional description field."""
    token = get_admin_token()
    client.preserve_context = False
    response = client.post('/quiz', 
        json={
            'name': f'No Description Quiz {uuid.uuid4()}',
            'category_name': TEST_CATEGORY_NAME
            # No description field
        },
        headers={'Authorization': f'Bearer {token}'}
    )
    assert response.status_code == 201
    quiz_id = response.json['unique_id']
    
    # Verify quiz was created with empty description
    quiz_response = client.get(f'/quiz/{quiz_id}')
    assert quiz_response.json['description'] is None or quiz_response.json['description'] == ''
    
    # Clean up
    client.delete(f'/quiz/{quiz_id}', headers={'Authorization': f'Bearer {token}'})

# Testing JWT authentication
def test_jwt_token_expiration(client):
    """Test behavior when JWT token is expired."""
    # This is a mock test since we can't easily manipulate token expiration
    # We can test with an invalid token though
    response = client.post('/category', 
        json={'name': 'New Category'},
        headers={'Authorization': 'Bearer invalid_token'}
    )
    assert response.status_code == 422  # JWT decode error
def test_wrong_user_identity(client):
    """Test access with a valid token but wrong identity."""
    # Create a token for a non-admin user
    with client.application.app_context():
        from flask_jwt_extended import create_access_token
        non_admin_token = create_access_token(identity="non_admin")
        
    # Try to access admin-only endpoint
    response = client.post('/category', 
        json={'name': 'New Category Test'},
        headers={'Authorization': f'Bearer {non_admin_token}'}
    )
    assert response.status_code == 403
    assert "Unauthorized" in response.json["msg"]
