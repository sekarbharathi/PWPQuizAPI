# PWP SPRING 2025
# QUIZ
# Group information
* Student 1. Bharathi Sekar and Bharathi.Sekar@student.oulu.fi
* Student 2. Chamudi Vidanagama and Chamudi.Vidanagama@student.oulu.fi
* Student 3. An Vu and qvu24@student.oulu.fi


### DEPENDENCIES

#### This project requires the following external libraries:

Flask - A lightweight web framework for Python.

SQLAlchemy - An SQL toolkit and ORM for Python.

Flask-SQLAlchemy - A Flask extension for integrating SQLAlchemy.

#### To install all dependencies, run the following command:

    pip install sqlalchemy flask flask_sqlalchemy

#### INSTALLING DEPENDENCIES Using requirements.txt

**Create a Virtual Environment**

Before installing dependencies, create and activate a virtual environment:

**Windows:**

    python -m venv venv
    venv\Scripts\activate
    
**macOS/Linux:**

    python -m venv venv
    source venv/bin/activate
    
**Install Dependencies**

Run the following command to install all required packages:

    pip install -r requirements.txt

### Database Setup

#### Database Type and Version

This project uses SQLite (version 3.45.3) as the database. SQLite is a lightweight, file-based relational database engine, making it ideal for local development and small-scale applications.

#### Installation and Setup

**Install Required Dependencies**

Ensure you have installed the necessary dependencies as mentioned above.

**Database Configuration**

The database configuration is defined in config.py

**Initialize the Database**

Database initialization is handled in init_db.py

To initialize the database,run:

    python database.py


**Populating the Database**

**1. Automatically Populate Data**

To insert sample data (categories, quizzes, questions, and options), run:

    python populatepy

This script will:

  Create categories
  
  Create quizzes and associate them with categories
  
  Create questions and link them to quizzes
  
  Add multiple-choice options to each question


**2. Manual Data Insertion**

You can manually insert data into the database using an SQLite browser.

**For visualizing the database**

Download SQLite from https://sqlitebrowser.org/ and use database.db file.


### Running the Application

To run the application, use the following command:

    flask run

The API will be available at http://127.0.0.1:5000.

### API Endpoints

#### Authentication

POST /login: Authenticate and get a JWT token.

#### Categories

GET /category - List all categories  

POST /category - Create category (Admin)

PUT /category/<category_name> - Update category (Admin)  

DELETE /category/<category_name> - Delete category (Admin)

#### Quizzes

GET /quiz - List all quizzes

POST /quiz - Create quiz (Admin)

PUT /quiz/<quiz_unique_id> - Update quiz (Admin)

DELETE /quiz/<quiz_unique_id> - Delete quiz (Admin)

#### Questions

GET /question - List all questions

GET /question/<question_unique_id> - Get question details

POST /question - Create question (Admin)  

PUT /question/<question_unique_id> - Update question (Admin)

DELETE /question/<question_unique_id> - Delete question (Admin)


#### Filtering

GET /category/<category_name>/quizzes - Get quizzes by category

GET /quiz/<quiz_unique_id>/questions - Get questions by quiz

GET /category/<category_name>/quiz/<quiz_name>/all - Get all quiz questions  

GET /category/<category_name>/quiz/<quiz_name>/questions?question_count=%&complex_level=% - Get filtered questions with parameters

### Test the API:

Use tools like Postman or curl to test the endpoints.

### API Documentation

View the complete API documentation in Swagger Editor: quiz-api-docs.yaml


### Running Tests

To run the tests and check coverage, use the following command:

    python -m pytest --cov=app --cov-report=term-missing


FLASK_APP=app.app FLASK_ENV=development flask run