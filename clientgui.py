import sys
import json
from getpass import getpass
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QListWidget, QStackedWidget, QLineEdit,
                             QTextEdit, QComboBox, QRadioButton, QButtonGroup, QMessageBox,
                             QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog,
                             QDialog, QDialogButtonBox, QComboBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

API_BASE_URL = "http://127.0.0.1:5000"
ADMIN_USERNAME = "admin"

class QuizClientGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quiz API Client")
        self.resize(800, 600)
        
        self.token = None
        self.is_admin = False
        self.categories = []
        self.quizzes = []
        self.questions = []
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QHBoxLayout(self.central_widget)
        
        # Sidebar menu
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(200)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        
        self.mode_label = QLabel("USER MODE")
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setStyleSheet("font-weight: bold; color: orange;")
        
        self.menu_buttons = {
            "Browse Content": QPushButton("Browse Content"),
            "Take a Quiz": QPushButton("Take a Quiz"),
            "Admin Login": QPushButton("Admin Login"),
            "Exit": QPushButton("Exit")
        }
        
        self.sidebar_layout.addWidget(self.mode_label)
        for button in self.menu_buttons.values():
            button.setStyleSheet("text-align: left; padding: 8px;")
            self.sidebar_layout.addWidget(button)
        self.sidebar_layout.addStretch()
        
        # Main content area
        self.stacked_widget = QStackedWidget()
        
        # Login page
        self.login_page = QWidget()
        self.setup_login_page()
        self.stacked_widget.addWidget(self.login_page)
        
        # Main menu page
        self.main_menu_page = QWidget()
        self.stacked_widget.addWidget(self.main_menu_page)
        
        # Browse content pages
        self.browse_content_page = QWidget()
        self.setup_browse_content_page()
        self.stacked_widget.addWidget(self.browse_content_page)
        
        # Quiz flow pages
        self.quiz_flow_page = QWidget()
        self.setup_quiz_flow_page()
        self.stacked_widget.addWidget(self.quiz_flow_page)
        
        # Admin management pages
        self.admin_manage_page = QWidget()
        self.setup_admin_manage_page()
        self.stacked_widget.addWidget(self.admin_manage_page)
        
        self.layout.addWidget(self.sidebar)
        self.layout.addWidget(self.stacked_widget)
        
        self.connect_signals()
        self.load_resources()
        self.show_main_menu()
    
    def connect_signals(self):
        self.menu_buttons["Browse Content"].clicked.connect(self.show_browse_content)
        self.menu_buttons["Take a Quiz"].clicked.connect(self.start_quiz_flow)
        self.menu_buttons["Admin Login"].clicked.connect(self.show_login_page)
        self.menu_buttons["Exit"].clicked.connect(self.close)
    
    def setup_login_page(self):
        layout = QVBoxLayout(self.login_page)
        
        title = QLabel("Admin Login")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        login_button = QPushButton("Login")
        login_button.clicked.connect(self.handle_login)
        
        back_button = QPushButton("Back to Main Menu")
        back_button.clicked.connect(self.show_main_menu)
        
        layout.addWidget(title)
        layout.addWidget(QLabel("Username:"))
        layout.addWidget(self.username_input)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)
        layout.addWidget(back_button)
        layout.addStretch()
    
    def setup_browse_content_page(self):
        layout = QVBoxLayout(self.browse_content_page)
        
        self.browse_title = QLabel()
        self.browse_title.setFont(QFont("Arial", 14, QFont.Bold))
        
        self.content_table = QTableWidget()
        self.content_table.setColumnCount(3)
        self.content_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.content_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.content_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.detail_view = QTextEdit()
        self.detail_view.setReadOnly(True)
        
        back_button = QPushButton("Back to Browse Menu")
        back_button.clicked.connect(self.show_browse_content)
        
        layout.addWidget(self.browse_title)
        layout.addWidget(self.content_table)
        layout.addWidget(self.detail_view)
        layout.addWidget(back_button)
    
    def setup_quiz_flow_page(self):
        layout = QVBoxLayout(self.quiz_flow_page)
        
        self.quiz_title = QLabel()
        self.quiz_title.setFont(QFont("Arial", 14, QFont.Bold))
        
        self.quiz_question = QLabel()
        self.quiz_question.setWordWrap(True)
        
        self.quiz_options = QButtonGroup()
        self.quiz_options_layout = QVBoxLayout()
        
        self.quiz_progress = QLabel()
        
        submit_button = QPushButton("Submit Answer")
        submit_button.clicked.connect(self.handle_quiz_answer)
        
        back_button = QPushButton("Cancel Quiz")
        back_button.clicked.connect(self.show_main_menu)
        
        options_widget = QWidget()
        options_widget.setLayout(self.quiz_options_layout)
        
        layout.addWidget(self.quiz_title)
        layout.addWidget(self.quiz_progress)
        layout.addWidget(self.quiz_question)
        layout.addWidget(options_widget)
        layout.addWidget(submit_button)
        layout.addWidget(back_button)
        layout.addStretch()
    
    def setup_admin_manage_page(self):
        layout = QVBoxLayout(self.admin_manage_page)
        
        self.admin_title = QLabel("Admin Management")
        self.admin_title.setFont(QFont("Arial", 14, QFont.Bold))
        
        self.admin_table = QTableWidget()
        self.admin_table.setColumnCount(3)
        self.admin_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.admin_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.admin_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Create")
        self.update_button = QPushButton("Update")
        self.delete_button = QPushButton("Delete")
        
        # Initialize with empty connections
        self.create_button.clicked.connect(lambda: None)
        self.update_button.clicked.connect(lambda: None)
        self.delete_button.clicked.connect(lambda: None)
        
        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.delete_button)
        
        back_button = QPushButton("Back to Admin Menu")
        back_button.clicked.connect(self.show_admin_menu)
        
        layout.addWidget(self.admin_title)
        layout.addWidget(self.admin_table)
        layout.addLayout(button_layout)
        layout.addWidget(back_button)
    
    def _make_request(self, method, endpoint, data=None):
        url = f"{API_BASE_URL}{endpoint}"
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            response = requests.request(
                method,
                url,
                json=data,
                headers=headers
            )
            
            if response.status_code >= 400:
                self._handle_error(response)
                return None
                
            return response.json() if response.content else None
            
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Network error: {str(e)}")
            return None
    
    def _handle_error(self, response):
        try:
            error_data = response.json()
            msg = error_data.get('msg', 'Unknown error')
        except ValueError:
            msg = response.text or 'Unknown error'
            
        QMessageBox.critical(self, f"Error {response.status_code}", msg)
    
    def load_resources(self):
        self.categories = self._get_categories()
        self.quizzes = self._get_quizzes()
        self.questions = self._get_questions()
    
    def _get_categories(self):
        response = self._make_request("GET", "/category")
        return response.get('categories', []) if response else []
    
    def _get_quizzes(self):
        response = self._make_request("GET", "/quiz")
        return response.get('quizzes', []) if response else []
    
    def _get_questions(self):
        response = self._make_request("GET", "/question")
        return response.get('questions', []) if response else []
    
    def _get_quizzes_by_category(self, category_name):
        response = self._make_request("GET", f"/category/{category_name}/quizzes")
        return response.get('quizzes', []) if response else []
    
    def _get_questions_by_quiz(self, quiz_id):
        response = self._make_request("GET", f"/quiz/{quiz_id}/questions")
        return response.get('questions', []) if response else []
    
    def show_main_menu(self):
        self.stacked_widget.setCurrentWidget(self.main_menu_page)
    
    def show_login_page(self):
        self.username_input.clear()
        self.password_input.clear()
        self.stacked_widget.setCurrentWidget(self.login_page)
    
    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        response = self._make_request("POST", "/login", data={
            "username": username,
            "password": password
        })
        
        if response and 'access_token' in response:
            self.token = response['access_token']
            self.is_admin = True
            self.mode_label.setText("ADMIN MODE")
            self.mode_label.setStyleSheet("font-weight: bold; color: green;")
            self.menu_buttons["Admin Login"].setText("Admin Tools")
            self.menu_buttons["Admin Login"].clicked.disconnect()  # Disconnect previous handler
            self.menu_buttons["Admin Login"].clicked.connect(self.show_admin_menu)  # Connect to admin menu
            self.menu_buttons["Take a Quiz"].setVisible(False)
            QMessageBox.information(self, "Success", "Admin login successful!")
            self.show_main_menu()
        else:
            QMessageBox.warning(self, "Error", "Invalid admin credentials")
    
    def show_browse_content(self):
        self.stacked_widget.setCurrentWidget(self.browse_content_page)
        self.show_browse_menu()
    
    def show_browse_menu(self):
        self.browse_title.setText("Browse Content")
        self.content_table.clear()
        self.content_table.setRowCount(3)
        self.content_table.setColumnCount(1)
        self.content_table.setHorizontalHeaderLabels(["Options"])
        
        items = ["Categories", "Quizzes", "Questions"]
        for row, item in enumerate(items):
            self.content_table.setItem(row, 0, QTableWidgetItem(item))
        
        self.content_table.cellClicked.connect(self.handle_browse_selection)
        self.detail_view.clear()
    
    def handle_browse_selection(self, row, col):
        if self.browse_title.text() == "Browse Content":
            if row == 0:
                self.show_categories()
            elif row == 1:
                self.show_quizzes()
            elif row == 2:
                self.show_questions()
        elif "Categories" in self.browse_title.text():
            self.show_category_detail(self.categories[row])
        elif "Quizzes" in self.browse_title.text():
            self.show_quiz_detail(self.quizzes[row])
        elif "Questions" in self.browse_title.text():
            self.show_question_detail(self.questions[row])
    
    def show_categories(self):
        self.browse_title.setText("Categories")
        self.content_table.clear()
        self.content_table.setRowCount(len(self.categories))
        self.content_table.setColumnCount(1)
        self.content_table.setHorizontalHeaderLabels(["Category Name"])
        
        for row, category in enumerate(self.categories):
            self.content_table.setItem(row, 0, QTableWidgetItem(category['name']))
        
        self.detail_view.clear()
    
    def show_category_detail(self, category):
        response = self._make_request("GET", f"/category/{category['name']}")
        if not response:
            return
            
        quizzes = self._get_quizzes_by_category(category['name'])
        detail_text = (
            f"<h2>{response['name']}</h2>"
            f"<p>Contains {len(quizzes)} quizzes</p>"
        )
        
        if quizzes:
            detail_text += "<h3>Quizzes in this category:</h3><ul>"
            for quiz in quizzes:
                detail_text += f"<li>{quiz['name']} - {quiz['description']}</li>"
            detail_text += "</ul>"
        
        self.detail_view.setHtml(detail_text)
    
    def show_quizzes(self):
        self.browse_title.setText("Quizzes")
        self.content_table.clear()
        self.content_table.setRowCount(len(self.quizzes))
        self.content_table.setColumnCount(2)
        self.content_table.setHorizontalHeaderLabels(["Quiz Name", "Description"])
        
        for row, quiz in enumerate(self.quizzes):
            self.content_table.setItem(row, 0, QTableWidgetItem(quiz['name']))
            self.content_table.setItem(row, 1, QTableWidgetItem(quiz.get('description', '')))
        
        self.detail_view.clear()
    
    def show_quiz_detail(self, quiz):
        response = self._make_request("GET", f"/quiz/{quiz['unique_id']}")
        if not response:
            return
            
        questions = self._get_questions_by_quiz(quiz['unique_id'])
        detail_text = (
            f"<h2>{response['name']}</h2>"
            f"<p><i>{response['description']}</i></p>"
            f"<p>Category: {response.get('category', 'N/A')}</p>"
            f"<p>Questions: {len(questions)}</p>"
        )
        
        if questions:
            detail_text += "<h3>Questions in this quiz:</h3><ul>"
            for question in questions:
                detail_text += f"<li>{question['question_statement']} ({question['complex_level']})</li>"
            detail_text += "</ul>"
        
        self.detail_view.setHtml(detail_text)
    
    def show_questions(self):
        self.browse_title.setText("Questions")
        self.content_table.clear()
        self.content_table.setRowCount(len(self.questions))
        self.content_table.setColumnCount(2)
        self.content_table.setHorizontalHeaderLabels(["Question", "Complexity"])
        
        for row, question in enumerate(self.questions):
            self.content_table.setItem(row, 0, QTableWidgetItem(question['question_statement']))
            self.content_table.setItem(row, 1, QTableWidgetItem(question['complex_level']))
        
        self.detail_view.clear()
    
    def show_question_detail(self, question):
        response = self._make_request("GET", f"/question/{question['unique_id']}")
        if not response:
            return
            
        options_text = "<h3>Options:</h3><ul>"
        for opt in response['options']:
            if self.is_admin:
                options_text += f"<li>{opt['option_statement']} {'✓' if opt['is_correct'] else ''}</li>"
            else:
                options_text += f"<li>{opt['option_statement']}</li>"
        options_text += "</ul>"
        
        detail_text = (
            f"<h2>{response['question_statement']}</h2>"
            f"<p>Complexity: {response['complex_level']}</p>"
            f"{options_text}"
        )
        
        self.detail_view.setHtml(detail_text)
    
    def start_quiz_flow(self):
        if not self.categories:
            QMessageBox.warning(self, "Error", "No categories available")
            return
            
        category, ok = QInputDialog.getItem(
            self, "Select Category", "Choose a category:",
            [cat['name'] for cat in self.categories], 0, False
        )
        
        if not ok:
            return
            
        quizzes = self._get_quizzes_by_category(category)
        if not quizzes:
            QMessageBox.warning(self, "Error", f"No quizzes found in {category}")
            return
            
        quiz, ok = QInputDialog.getItem(
            self, "Select Quiz", "Choose a quiz:",
            [f"{q['name']} - {q['description']}" for q in quizzes], 0, False
        )
        
        if not ok:
            return
            
        quiz_id = quizzes[[f"{q['name']} - {q['description']}" for q in quizzes].index(quiz)]['unique_id']
        questions = self._get_questions_by_quiz(quiz_id)
        
        if not questions:
            QMessageBox.warning(self, "Error", "No questions found in this quiz")
            return
            
        complexity, ok = QInputDialog.getItem(
            self, "Select Complexity", "Choose complexity level:",
            ["easy", "medium", "hard", "all"], 0, False
        )
        
        if not ok:
            return
            
        if complexity != "all":
            questions = [q for q in questions if q['complex_level'] == complexity]
            if not questions:
                QMessageBox.warning(self, "Error", f"No {complexity} questions found")
                return
                
        count, ok = QInputDialog.getInt(
            self, "Number of Questions", 
            f"Enter number of questions (1-{len(questions)}):",
            min(5, len(questions)), 1, len(questions), 1
        )
        
        if not ok:
            return
            
        self.current_quiz = {
            "name": quiz.split(" - ")[0],
            "questions": questions[:count],
            "current_question": 0,
            "score": 0
        }
        
        self.show_quiz_question()
    
    def show_quiz_question(self):
        self.stacked_widget.setCurrentWidget(self.quiz_flow_page)
        
        question = self.current_quiz['questions'][self.current_quiz['current_question']]
        response = self._make_request("GET", f"/question/{question['unique_id']}")
        if not response:
            return
            
        self.quiz_title.setText(f"Quiz: {self.current_quiz['name']}")
        self.quiz_progress.setText(
            f"Question {self.current_quiz['current_question'] + 1}/{len(self.current_quiz['questions'])} | "
            f"Score: {self.current_quiz['score']}/{self.current_quiz['current_question']}"
        )
        
        self.quiz_question.setText(response['question_statement'])
        
        # Clear previous options
        for i in reversed(range(self.quiz_options_layout.count())): 
            self.quiz_options_layout.itemAt(i).widget().setParent(None)
        self.quiz_options = QButtonGroup()
        
        for i, opt in enumerate(response['options']):
            radio = QRadioButton(opt['option_statement'])
            self.quiz_options.addButton(radio, i)
            self.quiz_options_layout.addWidget(radio)
    
    def handle_quiz_answer(self):
        if not self.quiz_options.checkedButton():
            QMessageBox.warning(self, "Error", "Please select an answer")
            return
            
        question = self.current_quiz['questions'][self.current_quiz['current_question']]
        response = self._make_request("GET", f"/question/{question['unique_id']}")
        if not response:
            return
            
        selected_index = self.quiz_options.checkedId()
        if response['options'][selected_index]['is_correct']:
            self.current_quiz['score'] += 1
            QMessageBox.information(self, "Correct", "✓ Correct answer!")
        else:
            correct_index = next(i for i, opt in enumerate(response['options']) if opt['is_correct'])
            QMessageBox.warning(
                self, "Incorrect", 
                f"✗ Incorrect! The correct answer was: {response['options'][correct_index]['option_statement']}"
            )
        
        self.current_quiz['current_question'] += 1
        
        if self.current_quiz['current_question'] < len(self.current_quiz['questions']):
            self.show_quiz_question()
        else:
            self.show_quiz_results()
    
    def show_quiz_results(self):
        percentage = (self.current_quiz['score'] / len(self.current_quiz['questions'])) * 100
        if percentage >= 70:
            message = "Excellent!"
            color = "green"
        elif percentage >= 50:
            message = "Good effort!"
            color = "orange"
        else:
            message = "Keep practicing!"
            color = "red"
        
        result_text = (
            f"<h2>Quiz Complete!</h2>"
            f"<p>Correct Answers: <b>{self.current_quiz['score']}/{len(self.current_quiz['questions'])}</b></p>"
            f"<p>Percentage: <b style='color:{color}'>{percentage:.0f}%</b></p>"
            f"<p>{message}</p>"
        )
        
        self.detail_view.setHtml(result_text)
        self.stacked_widget.setCurrentWidget(self.browse_content_page)
    
    def show_admin_menu(self):
        if not self.is_admin:
            QMessageBox.warning(self, "Error", "Admin privileges required")
            if QMessageBox.question(self, "Login", "Do you want to login as admin now?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
                self.show_login_page()
            return
        
        self.stacked_widget.setCurrentWidget(self.admin_manage_page)
        self.show_admin_manage_menu()
    
    def show_admin_manage_menu(self):
        self.admin_title.setText("Admin Management")
        self.admin_table.clear()
        self.admin_table.setRowCount(4)
        self.admin_table.setColumnCount(1)
        self.admin_table.setHorizontalHeaderLabels(["Options"])
        
        items = ["Manage Categories", "Manage Quizzes", "Manage Questions", "Logout"]
        for row, item in enumerate(items):
            self.admin_table.setItem(row, 0, QTableWidgetItem(item))
        
        self.admin_table.cellClicked.connect(self.handle_admin_menu_selection)
    
    def handle_admin_menu_selection(self, row, col):
        try:
            if row == 0:
                self.manage_categories()
            elif row == 1:
                self.manage_quizzes()
            elif row == 2:
                self.manage_questions()
            elif row == 3:
                self.logout()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
    
    def manage_categories(self):
        self.admin_title.setText("Category Management")
        self.admin_table.clear()
        self.admin_table.setRowCount(len(self.categories))
        self.admin_table.setColumnCount(1)
        self.admin_table.setHorizontalHeaderLabels(["Category Name"])
        
        for row, category in enumerate(self.categories):
            self.admin_table.setItem(row, 0, QTableWidgetItem(category['name']))
            self.admin_table.item(row, 0).setData(Qt.UserRole, category)  # Store full category data
        
        # Disconnect any existing connections safely
        try:
            self.create_button.clicked.disconnect()
        except:
            pass
        try:
            self.update_button.clicked.disconnect()
        except:
            pass
        try:
            self.delete_button.clicked.disconnect()
        except:
            pass
        
        # Connect new handlers
        self.create_button.clicked.connect(self.create_category)
        self.update_button.clicked.connect(self.update_category)
        self.delete_button.clicked.connect(self.delete_category)
    
    def create_category(self):
        name, ok = QInputDialog.getText(self, "Create Category", "Enter category name:")
        if ok and name:
            response = self._make_request("POST", "/category", data={"name": name})
            if response and response.get('msg') == "Category created":
                QMessageBox.information(self, "Success", "Category created successfully!")
                self.categories = self._get_categories()
                self.manage_categories()
            else:
                QMessageBox.warning(self, "Error", "Failed to create category")
    
    def update_category(self):
        selected_row = self.admin_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a category to update")
            return
        
        category = self.admin_table.item(selected_row, 0).data(Qt.UserRole)
        new_name, ok = QInputDialog.getText(
            self, "Update Category", 
            "Enter new category name:", 
            text=category['name']
        )
        
        if ok and new_name:
            response = self._make_request(
                "PUT", f"/category/{category['name']}", 
                data={"name": new_name}
            )
            
            if response and response.get('msg') == "Category updated":
                QMessageBox.information(self, "Success", "Category updated successfully!")
                self.categories = self._get_categories()
                self.manage_categories()
            else:
                QMessageBox.warning(self, "Error", "Failed to update category")
    
    def delete_category(self):
        selected_row = self.admin_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a category to delete")
            return
        
        category = self.admin_table.item(selected_row, 0).data(Qt.UserRole)
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete '{category['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            response = self._make_request("DELETE", f"/category/{category['name']}")
            if response and response.get('msg') == "Category deleted":
                QMessageBox.information(self, "Success", "Category deleted successfully!")
                self.categories = self._get_categories()
                self.manage_categories()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete category")
    
    def manage_quizzes(self):
        self.admin_title.setText("Quiz Management")
        self.admin_table.clear()
        self.admin_table.setRowCount(len(self.quizzes))
        self.admin_table.setColumnCount(2)
        self.admin_table.setHorizontalHeaderLabels(["Quiz Name", "Description"])
        
        for row, quiz in enumerate(self.quizzes):
            self.admin_table.setItem(row, 0, QTableWidgetItem(quiz['name']))
            self.admin_table.setItem(row, 1, QTableWidgetItem(quiz.get('description', '')))
            self.admin_table.item(row, 0).setData(Qt.UserRole, quiz)  # Store full quiz data
        
        # Disconnect any existing connections safely
        try:
            self.create_button.clicked.disconnect()
        except:
            pass
        try:
            self.update_button.clicked.disconnect()
        except:
            pass
        try:
            self.delete_button.clicked.disconnect()
        except:
            pass
        
        # Connect new handlers
        self.create_button.clicked.connect(self.create_quiz)
        self.update_button.clicked.connect(self.update_quiz)
        self.delete_button.clicked.connect(self.delete_quiz)
    
    def create_quiz(self):
        name, ok = QInputDialog.getText(self, "Create Quiz", "Enter quiz name:")
        if not ok or not name:
            return
            
        description, ok = QInputDialog.getText(
            self, "Create Quiz", "Enter quiz description:"
        )
        if not ok:
            return
            
        category, ok = QInputDialog.getItem(
            self, "Select Category", "Choose a category:",
            [cat['name'] for cat in self.categories], 0, False
        )
        if not ok:
            return
            
        response = self._make_request("POST", "/quiz", data={
            "name": name,
            "description": description,
            "category_name": category
        })
        
        if response and response.get('msg') == "Quiz created":
            QMessageBox.information(self, "Success", "Quiz created successfully!")
            self.quizzes = self._get_quizzes()
            self.manage_quizzes()
        else:
            QMessageBox.warning(self, "Error", "Failed to create quiz")
    
    def update_quiz(self):
        selected_row = self.admin_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a quiz to update")
            return
        
        quiz = self.admin_table.item(selected_row, 0).data(Qt.UserRole)
        
        # Get current values
        current_name = quiz['name']
        current_description = quiz.get('description', '')
        current_category = quiz.get('category', '')
        
        # Create a custom dialog for quiz update
        dialog = QDialog(self)
        dialog.setWindowTitle("Update Quiz")
        layout = QVBoxLayout()
        
        # Quiz name
        name_label = QLabel("Quiz Name:")
        name_input = QLineEdit(current_name)
        layout.addWidget(name_label)
        layout.addWidget(name_input)
        
        # Description
        desc_label = QLabel("Description:")
        desc_input = QLineEdit(current_description)
        layout.addWidget(desc_label)
        layout.addWidget(desc_input)
        
        # Category selection
        category_label = QLabel("Category:")
        category_combo = QComboBox()
        category_combo.addItems([cat['name'] for cat in self.categories])
        if current_category in [cat['name'] for cat in self.categories]:
            category_combo.setCurrentText(current_category)
        layout.addWidget(category_label)
        layout.addWidget(category_combo)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            name = name_input.text().strip()
            description = desc_input.text().strip()
            category = category_combo.currentText()
            
            if not name:
                QMessageBox.warning(self, "Error", "Quiz name cannot be empty")
                return
                
            response = self._make_request(
                "PUT", f"/quiz/{quiz['unique_id']}", 
                data={
                    "name": name,
                    "description": description,
                    "category_name": category
                }
            )
            
            if response and response.get('msg') == "Quiz updated":
                QMessageBox.information(self, "Success", "Quiz updated successfully!")
                self.quizzes = self._get_quizzes()
                self.manage_quizzes()
            else:
                QMessageBox.warning(self, "Error", "Failed to update quiz")

    def delete_quiz(self):
        selected_row = self.admin_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a quiz to delete")
            return
        
        quiz = self.admin_table.item(selected_row, 0).data(Qt.UserRole)
        
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete '{quiz['name']}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            response = self._make_request("DELETE", f"/quiz/{quiz['unique_id']}")
            if response and response.get('msg') == "Quiz deleted":
                QMessageBox.information(self, "Success", "Quiz deleted successfully!")
                self.quizzes = self._get_quizzes()
                self.manage_quizzes()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete quiz")

    def manage_questions(self):
        self.admin_title.setText("Question Management")
        self.admin_table.clear()
        self.admin_table.setRowCount(len(self.questions))
        self.admin_table.setColumnCount(2)
        self.admin_table.setHorizontalHeaderLabels(["Question", "Complexity"])
        
        for row, question in enumerate(self.questions):
            self.admin_table.setItem(row, 0, QTableWidgetItem(question['question_statement']))
            self.admin_table.setItem(row, 1, QTableWidgetItem(question['complex_level']))
            self.admin_table.item(row, 0).setData(Qt.UserRole, question)  # Store full question data
        
        # Disconnect any existing connections safely
        try:
            self.create_button.clicked.disconnect()
        except:
            pass
        try:
            self.update_button.clicked.disconnect()
        except:
            pass
        try:
            self.delete_button.clicked.disconnect()
        except:
            pass
        
        # Connect new handlers
        self.create_button.clicked.connect(self.create_question)
        self.update_button.clicked.connect(self.update_question)
        self.delete_button.clicked.connect(self.delete_question)
    
    def create_question(self):
        # This is a simplified version - you may want to create a custom dialog
        # for question creation with all the options
        statement, ok = QInputDialog.getText(
            self, "Create Question", "Enter question statement:"
        )
        if not ok or not statement:
            return
            
        complexity, ok = QInputDialog.getItem(
            self, "Select Complexity", "Choose complexity level:",
            ["easy", "medium", "hard"], 0, False
        )
        if not ok:
            return
            
        quiz, ok = QInputDialog.getItem(
            self, "Select Quiz", "Choose a quiz:",
            [f"{q['name']} - {q['description']}" for q in self.quizzes], 0, False
        )
        if not ok:
            return
            
        quiz_id = self.quizzes[[f"{q['name']} - {q['description']}" for q in self.quizzes].index(quiz)]['unique_id']
        
        # For simplicity, we'll just create with 2 options
        options = []
        for i in range(2):
            option_text, ok = QInputDialog.getText(
                self, f"Option {i+1}", f"Enter option {i+1} text:"
            )
            if not ok or not option_text:
                return
                
            is_correct = (i == 0)  # First option is correct by default
            options.append({
                "option_statement": option_text,
                "is_correct": is_correct
            })
        
        response = self._make_request("POST", "/question", data={
            "question_statement": statement,
            "complex_level": complexity,
            "quiz_unique_id": quiz_id,
            "options": options
        })
        
        if response and response.get('msg') == "Question created":
            QMessageBox.information(self, "Success", "Question created successfully!")
            self.questions = self._get_questions()
            self.manage_questions()
        else:
            QMessageBox.warning(self, "Error", "Failed to create question")
    
    def update_question(self):
        selected_row = self.admin_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a question to update")
            return
        
        question = self.admin_table.item(selected_row, 0).data(Qt.UserRole)
        
        # Get full question details from API
        response = self._make_request("GET", f"/question/{question['unique_id']}")
        if not response:
            QMessageBox.warning(self, "Error", "Failed to load question details")
            return
        
        question_data = response
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Update Question")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        
        # Question statement
        stmt_label = QLabel("Question:")
        stmt_input = QTextEdit(question_data['question_statement'])
        layout.addWidget(stmt_label)
        layout.addWidget(stmt_input)
        
        # Complexity
        complex_label = QLabel("Complexity:")
        complex_combo = QComboBox()
        complex_combo.addItems(["easy", "medium", "hard"])
        complex_combo.setCurrentText(question_data['complex_level'])
        layout.addWidget(complex_label)
        layout.addWidget(complex_combo)
        
        # Quiz selection
        quiz_label = QLabel("Quiz:")
        quiz_combo = QComboBox()
        quizzes = [f"{q['name']} (ID: {q['unique_id']})" for q in self.quizzes]
        quiz_ids = [q['unique_id'] for q in self.quizzes]
        quiz_combo.addItems(quizzes)
        
        # Set current quiz if available
        if 'quiz_unique_id' in question_data:
            try:
                idx = quiz_ids.index(question_data['quiz_unique_id'])
                quiz_combo.setCurrentIndex(idx)
            except ValueError:
                pass
        
        layout.addWidget(quiz_label)
        layout.addWidget(quiz_combo)
        
        # Options
        options_label = QLabel("Options:")
        layout.addWidget(options_label)
        
        options_group = QButtonGroup()
        options_layout = QVBoxLayout()
        
        # Get current options
        options = question_data.get('options', [])
        
        # Add option inputs
        option_widgets = []
        for i, opt in enumerate(options):
            hbox = QHBoxLayout()
            radio = QRadioButton()
            radio.setChecked(opt['is_correct'])
            options_group.addButton(radio, i)
            text_input = QLineEdit(opt['option_statement'])
            hbox.addWidget(radio)
            hbox.addWidget(text_input)
            option_widgets.append((radio, text_input))
            options_layout.addLayout(hbox)
        
        layout.addLayout(options_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec_() == QDialog.Accepted:
            # Prepare updated data
            updated_options = []
            for radio, text_input in option_widgets:
                updated_options.append({
                    "option_statement": text_input.text().strip(),
                    "is_correct": radio.isChecked()
                })
            
            # Validate at least one correct option
            if not any(opt['is_correct'] for opt in updated_options):
                QMessageBox.warning(self, "Error", "At least one option must be marked as correct")
                return
            
            # Get selected quiz ID
            selected_quiz_idx = quiz_combo.currentIndex()
            quiz_unique_id = quiz_ids[selected_quiz_idx]
            
            update_data = {
                "question_statement": stmt_input.toPlainText().strip(),
                "complex_level": complex_combo.currentText(),
                "quiz_unique_id": quiz_unique_id,
                "options": updated_options
            }
            
            # Validate required fields
            if not update_data['question_statement']:
                QMessageBox.warning(self, "Error", "Question statement cannot be empty")
                return
            
            response = self._make_request(
                "PUT", f"/question/{question['unique_id']}", 
                data=update_data
            )
            
            if response and response.get('msg') == "Question updated":
                QMessageBox.information(self, "Success", "Question updated successfully!")
                self.questions = self._get_questions()
                self.manage_questions()
            else:
                QMessageBox.warning(self, "Error", "Failed to update question")

    def delete_question(self):
        selected_row = self.admin_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a question to delete")
            return
        
        question = self.admin_table.item(selected_row, 0).data(Qt.UserRole)
        
        # Debug: Print question ID before deletion attempt
        print(f"Attempting to delete question with ID: {question['unique_id']}")
        
        # Create confirmation dialog
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this question?\n\n{question['question_statement']}",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                # Attempt deletion
                delete_response = self._make_request("DELETE", f"/question/{question['unique_id']}")
                
                # Debug: Print full API response
                print(f"Delete API response: {delete_response}")
                
                if delete_response and delete_response.get('msg') == 'Question and related records deleted':
                    QMessageBox.information(self, "Success", "Question deleted successfully!")
                    # Remove the question from the local list
                    self.questions = [q for q in self.questions if q['unique_id'] != question['unique_id']]
                    self.manage_questions()  # Refresh the table
                else:
                    error_msg = delete_response.get('msg', 'Unknown error') if delete_response else 'No response from server'
                    QMessageBox.warning(
                        self,
                        "Deletion Failed",
                        f"Failed to delete question:\n{error_msg}"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"An unexpected error occurred:\n{str(e)}"
                )
                print(f"Deletion error: {str(e)}")
    
    def logout(self):
        self.token = None
        self.is_admin = False
        self.mode_label.setText("USER MODE")
        self.mode_label.setStyleSheet("font-weight: bold; color: orange;")
        self.menu_buttons["Admin Login"].setText("Admin Login")
        self.menu_buttons["Admin Login"].clicked.disconnect()  # Disconnect admin menu handler
        self.menu_buttons["Admin Login"].clicked.connect(self.show_login_page)  # Reconnect to login
        self.menu_buttons["Take a Quiz"].setVisible(True)
        QMessageBox.information(self, "Success", "Successfully logged out")
        self.show_main_menu()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    client = QuizClientGUI()
    client.show()
    sys.exit(app.exec_())