"""Database population script for Quiz Application.

This script populates the database with sample categories, quizzes, questions,
and options for testing and demonstration purposes.
"""

from app.app import app, db
from app.models import Category, Quiz, Question, Option, QuizCategory, QuizQuestion


def create_category(name):
    """Create a new category in the database.

    Args:
        name (str): Name of the category to create

    Returns:
        Category: The created category object
    """
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return category


def create_quiz(name, description, categories):
    """Create a new quiz and link it to categories.

    Args:
        name (str): Name of the quiz
        description (str): Description of the quiz
        categories (list): List of Category objects to associate with the quiz

    Returns:
        Quiz: The created quiz object
    """
    quiz = Quiz(name=name, description=description)
    db.session.add(quiz)
    db.session.commit()

    # Create associations between quiz and categories
    for category in categories:
        quiz_category = QuizCategory(
            quiz_id=quiz.quiz_id, category_id=category.category_id
        )
        db.session.add(quiz_category)
    db.session.commit()
    return quiz


def create_question(question_statement, complex_level):
    """Create a new question in the database.

    Args:
        question_statement (str): The question text
        complex_level (str): Complexity level ('easy', 'medium', or 'hard')

    Returns:
        Question: The created question object
    """
    question = Question(
        question_statement=question_statement, complex_level=complex_level
    )
    db.session.add(question)
    db.session.commit()
    return question


def create_option(question, option_statement, is_correct):
    """Create an option for a question.

    Args:
        question (Question): The question this option belongs to
        option_statement (str): The option text
        is_correct (bool): Whether this option is correct
    """
    option = Option(
        question_id=question.question_id,
        option_statement=option_statement,
        is_correct=is_correct,
    )
    db.session.add(option)
    db.session.commit()


def create_quiz_question(quiz, question):
    """Link a question to a quiz.

    Args:
        quiz (Quiz): The quiz to link to
        question (Question): The question to link
    """
    quiz_question = QuizQuestion(quiz_id=quiz.quiz_id, question_id=question.question_id)
    db.session.add(quiz_question)
    db.session.commit()


def populate_data():
    """Populate the database with sample data including categories, quizzes,
    questions and options.
    """
    # Categories
    programming_languages_category = create_category("Programming Languages")

    # Quizzes (Python, Java, C, C++, C#, Kotlin)
    quizzes = [
        create_quiz(
            "Python Quiz",
            "Python Programming Language Questions",
            [programming_languages_category],
        ),
        create_quiz(
            "Java Quiz",
            "Java Programming Language Questions",
            [programming_languages_category],
        ),
        create_quiz(
            "C Quiz",
            "C Programming Language Questions",
            [programming_languages_category],
        ),
        create_quiz(
            "C++ Quiz",
            "C++ Programming Language Questions",
            [programming_languages_category],
        ),
        create_quiz(
            "C# Quiz",
            "C# Programming Language Questions",
            [programming_languages_category],
        ),
        create_quiz(
            "Kotlin Quiz",
            "Kotlin Programming Language Questions",
            [programming_languages_category],
        ),
    ]

    # Question statements and complexity levels
    question_statements = {
        "Python": [
            ("What is the output of print(2 + 3)?", ["2", "3", "5", "7"], "5"),
            (
                "Which method is used to add an element at the end of a list?",
                ["append()", "extend()", "insert()", "pop()"],
                "append()",
            ),
            (
                "What is the difference between shallow and deep copy in Python?",
                [
                    "Shallow copy copies references; deep copy copies values.",
                    "Shallow copy copies values; deep copy copies references.",
                    "There is no difference.",
                    "Shallow copy only works with objects.",
                ],
                "Shallow copy copies references; deep copy copies values.",
            ),
        ],
        "Java": [
            (
                "Which of the following is a valid data type in Java?",
                ["int", "float", "double", "all of the above"],
                "all of the above",
            ),
            (
                "What is the difference between String and StringBuilder in Java?",
                [
                    "StringBuilder is mutable, String is immutable.",
                    "StringBuilder is immutable, String is mutable.",
                    "Both are immutable.",
                    "StringBuilder is slower than String.",
                ],
                "StringBuilder is mutable, String is immutable.",
            ),
            (
                "Explain the concept of polymorphism in Java with an example?",
                [
                    "The ability to treat objects of different classes as "
                    "objects of a common superclass.",
                    "The ability of a method to perform different tasks.",
                    "The ability of a class to inherit methods from another class.",
                    "None of the above.",
                ],
                "The ability to treat objects of different classes as "
                "objects of a common superclass.",
            ),
        ],
        "C": [
            (
                "What does the 'printf' function do in C?",
                [
                    "Prints formatted output",
                    "Prints raw output",
                    "Prints only integers",
                    "Prints a newline",
                ],
                "Prints formatted output",
            ),
            (
                "What is the purpose of 'const' keyword in C?",
                [
                    "To define constant values",
                    "To define variables that cannot be changed",
                    "Both of the above",
                    "None of the above",
                ],
                "Both of the above",
            ),
            (
                "Explain the memory model of C and the importance of pointers?",
                [
                    "C uses stack memory only.",
                    "Pointers in C allow for direct access to memory, "
                    "helping with dynamic memory management.",
                    "C does not allow direct memory access.",
                    "None of the above.",
                ],
                "Pointers in C allow for direct access to memory, "
                "helping with dynamic memory management.",
            ),
        ],
        "C++": [
            (
                "What is the difference between a class and a structure in C++?",
                [
                    "Classes are private by default, structures are public by default.",
                    "Classes and structures are the same in C++.",
                    "Classes cannot have member functions.",
                    "Structures can inherit from classes.",
                ],
                "Classes are private by default, structures are public by default.",
            ),
            (
                "What is the purpose of virtual functions in C++?",
                [
                    "To allow for dynamic polymorphism.",
                    "To allow for multiple inheritance.",
                    "To prevent inheritance.",
                    "None of the above.",
                ],
                "To allow for dynamic polymorphism.",
            ),
            (
                "What is multiple inheritance and how does it work in C++?",
                [
                    "C++ supports multiple inheritance, allowing a class to "
                    "inherit from more than one base class.",
                    "C++ does not support multiple inheritance.",
                    "Multiple inheritance is not possible in C++ but is "
                    "supported in Java.",
                    "None of the above.",
                ],
                "C++ supports multiple inheritance, allowing a class to "
                "inherit from more than one base class.",
            ),
        ],
        "C#": [
            (
                "What is the use of 'using' keyword in C#?",
                [
                    "To include namespaces",
                    "To manage memory",
                    "To define variables",
                    "None of the above",
                ],
                "To include namespaces",
            ),
            (
                "What is the difference between value type and reference type in C#?",
                [
                    "Value types hold the actual value; reference types hold "
                    "a reference to the value.",
                    "There is no difference.",
                    "Value types are used for large objects; reference types "
                    "are for small ones.",
                    "None of the above.",
                ],
                "Value types hold the actual value; reference types hold "
                "a reference to the value.",
            ),
            (
                "What is dependency injection in C# and why is it useful?",
                [
                    "A design pattern to decouple classes and improve testability.",
                    "A method to increase performance by reusing instances.",
                    "A feature to avoid inheritance.",
                    "None of the above.",
                ],
                "A design pattern to decouple classes and improve testability.",
            ),
        ],
        "Kotlin": [
            (
                "What is the difference between 'var' and 'val' in Kotlin?",
                [
                    "'var' is mutable, 'val' is immutable.",
                    "'val' is mutable, 'var' is immutable.",
                    "'val' is used for functions, 'var' for variables.",
                    "None of the above.",
                ],
                "'var' is mutable, 'val' is immutable.",
            ),
            (
                "What are lambda expressions in Kotlin?",
                [
                    "Anonymous functions that can be passed around.",
                    "Functions that take another function as a parameter.",
                    "Both of the above.",
                    "None of the above.",
                ],
                "Both of the above.",
            ),
            (
                "Explain Kotlin's type system and how it handles null safety?",
                [
                    "Kotlin uses nullable and non-nullable types and provides "
                    "safe calls to handle null values.",
                    "Kotlin does not support null safety.",
                    "Kotlin does not allow for nullable types.",
                    "None of the above.",
                ],
                "Kotlin uses nullable and non-nullable types and provides "
                "safe calls to handle null values.",
            ),
        ],
    }

    # Add questions for each quiz
    for quiz, language in zip(quizzes, ["Python", "Java", "C", "C++", "C#", "Kotlin"]):
        for i, (question_statement, options, correct_option) in enumerate(
            question_statements[language]
        ):
            complex_level = ["easy", "medium", "hard"][i]
            question = create_question(question_statement, complex_level)

            # Create and assign options to the question
            for option in options:
                is_correct = option == correct_option
                create_option(question, option, is_correct)

            # Link question to quiz
            create_quiz_question(quiz, question)


if __name__ == "__main__":
    with app.app_context():
        populate_data()
    print("Database populated successfully!")
