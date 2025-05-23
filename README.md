# PWP SPRING 2025
# QUIZ
# Group information
* Student 1. An Vu and qvu24@student.oulu.fi
* Student 2. Bharathi Sekar and Bharathi.Sekar@student.oulu.fi
* Student 3. Chamudi Vidanagama and Chamudi.Vidanagama@student.oulu.fi

# Project Overview

## Dependencies

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

# Database Setup

#### Database Type and Version

This project uses SQLite (version 3.45.3) as the database. SQLite is a lightweight, file-based relational database engine, making it ideal for local development and small-scale applications.

#### Installation and Setup

**Install Required Dependencies**

Ensure you have installed the necessary dependencies as mentioned above.

**Database Configuration**

The database configuration is defined in config.py

**Initialize the Database**

Database initialization is handled in init_db.py

To initialize the database,run the below in root:

    python -m app.database


**Populating the Database**

**1. Automatically Populate Data**

To insert sample data (categories, quizzes, questions, and options), run the below in root:

    python -m app.populate

This script will:

  Create categories
  
  Create quizzes and associate them with categories
  
  Create questions and link them to quizzes
  
  Add multiple-choice options to each question


**2. Manual Data Insertion**

You can manually insert data into the database using an SQLite browser.

**For visualizing the database**

Download SQLite from https://sqlitebrowser.org/ and use database.db file.


# Running the Application

To run the application, use the following command in the root:

    export FLASK_APP=app.app
    flask run

The API will be available at http://127.0.0.1:5000.

# API Endpoints

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

# API Documentation

You can view the complete API documentation in the [Swagger Editor](https://editor.swagger.io/):

1. Open the Swagger Editor at the link above
2. Paste the contents of `quiz-api-docs.yaml` into the editor
3. The documentation will render automatically

# Running Test Coverage

To run the tests and check coverage, use the following command:

    python -m pytest --cov=app --cov-report=term-missing



# Deployment

The Quiz API can be deployed to Azure for reliability and scalability

To run the app deployed in Azure:

    FLASK_APP=app.app FLASK_ENV=development flask run

## Architecture
![image](https://github.com/user-attachments/assets/b103638d-8401-4e8b-845d-0945e5bfd1e6)

## Main Components

| Component | Role & Functionality | Necessity & Alternatives |
|-----------|----------------------|--------------------------|
| **Docker** | Containerization platform that packages the application and its dependencies, ensuring consistent environments across development and production. | **Necessity**: Provides isolation, consistency, and portability.<br>**Alternatives**: Virtual machines, traditional server deployments. |
| **Azure Container Registry (ACR)** | Private registry service for storing and managing Docker container images. | **Necessity**: Securely stores container images close to the deployment environment.<br>**Alternatives**: Docker Hub, Amazon ECR, GitHub Container Registry. |
| **Kubernetes (AKS)** | Container orchestration system managing deployment, scaling, and operations of application containers. | **Necessity**: Automates container management, provides scalability.<br>**Alternatives**: Docker Swarm, Amazon ECS. |
| **Flask** | Python web framework used to build the Quiz API application. | **Necessity**: Provides routing, request handling, and application structure.<br>**Alternatives**: Django, FastAPI. |
| **Gunicorn** | WSGI HTTP server for running Python web applications, serving as the application server. | **Necessity**: Manages worker processes efficiently.<br>**Alternatives**: uWSGI, Waitress. |
| **Supervisor** | Process control system for monitoring and controlling Gunicorn. | **Necessity**: Ensures application reliability by monitoring and auto-restarting processes.<br>**Alternatives**: systemd, Docker's restart policies. |
| **Nginx** | Web server acting as a reverse proxy in front of Gunicorn. | **Necessity**: Efficiently handles HTTP requests, provides buffering.<br>**Alternatives**: Apache HTTP Server, Caddy. |

## Before deploying ensure that you have:
- Azure CLI installed, have all required access to azure services like: AKS, ACR ...
- Docker installed
- kubectl installed
  
## Deployment Steps

Execute the deployment script: source deploy-to-azure.sh

## Cleanup

Execute the clean up script: source clean-azure.sh

# Client Setup

This project is a PyQt5-based GUI for quiz management, allowing users to interact with the quiz system through a user-friendly interface while offering comprehensive management capabilities for administrators. 

## Prerequisites

Before running the application, ensure you have the following dependencies installed:

- Python 3.6 or higher
- PyQt5
- requests

You can install these dependencies using requirements.txt

## Running the Client

1. Clone the Git repository and run the app. Make sure the API is running.

2. Navigate to the client directory:
   
       cd client
   
3. Run the PyQt5 GUI client:

        python clientgui.py

 This will launch the Quiz application with the graphical user interface.

