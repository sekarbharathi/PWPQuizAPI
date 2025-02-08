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

    python init_db.py


**Populating the Database**

**1. Automatically Populate Data**

To insert sample data (categories, quizzes, questions, and options), run:

    python generate_db.py

This script will:

  Create categories
  
  Create quizzes and associate them with categories
  
  Create questions and link them to quizzes
  
  Add multiple-choice options to each question


**2. Manual Data Insertion**

You can manually insert data into the database using an SQLite browser.

**For visualizing the database**

Download SQLite from https://sqlitebrowser.org/ and use database.db file.


