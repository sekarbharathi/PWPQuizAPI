# pylint: disable=no-name-in-module
# pylint: disable=too-many-lines

"""QuizApp Client - A PyQt5-based GUI for quiz management."""
import sys
import requests
from PyQt5.QtWidgets import (  # type: ignore
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QStackedWidget,
    QLineEdit,
    QTextEdit,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QInputDialog,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QListWidgetItem,
)
from PyQt5.QtCore import Qt, QSize, QTimer, QDateTime  # type: ignore
from PyQt5.QtGui import QIcon  # type: ignore


API_BASE_URL = "http://127.0.0.1:5000"
ADMIN_USERNAME = "admin"


class QuizClientGUI(QMainWindow):
    """Initialize main window, UI, and API connection."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QuizApp")
        self.setWindowIcon(QIcon("icons/quiz_icon.png"))
        self.resize(1000, 700)

        # Color scheme
        self.dark_purple = "#88304E"
        self.light_cream = "#F2EFE7"
        self.accent_color = "#4D8FD1"
        self.text_dark = "#000000"
        self.text_light = "#FFFFFF"

        # Style sheet
        self.setStyleSheet(
            f"""
            QMainWindow {{
                background-color: {self.dark_purple};
            }}
            QPushButton {{
                background-color: {self.accent_color};
                color: {self.text_light};
                border: none;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                font-size: 14px;
                margin: 4px 2px;
                border-radius: 10px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: #CE2D46;
            }}
            QPushButton:pressed {{
                background-color: #B8273D;
            }}
            QPushButton[flat="true"] {{
                background-color: transparent;
                color: {self.text_light};
                text-align: left;
                padding: 8px;
            }}
            QPushButton[flat="true"]:hover {{
                background-color: #9A2A4A;
            }}
            QLineEdit, QTextEdit, QComboBox {{
                padding: 6px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
                background-color: white;
            }}
            QTableWidget {{
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            QHeaderView::section {{
                background-color: {self.dark_purple};
                color: {self.text_light};
                padding: 8px;
                border: none;
            }}
            QLabel {{
                font-size: 14px;
                color: {self.text_dark};
            }}
            QRadioButton {{
                font-size: 14px;
                spacing: 8px;
                color: {self.text_dark};
            }}
            QTextEdit {{
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }}
            .sidebar {{
                background-color: {self.dark_purple};
                border-right: 1px solid #722B42;
            }}
            .sidebar QLabel {{
                color: {self.text_light};
                font-weight: bold;
                font-size: 16px;
                padding: 10px;
            }}
            .content-title {{
                font-size: 18px;
                font-weight: bold;
                color: {self.text_dark};
                margin-bottom: 15px;
            }}
            .admin-title {{
                font-size: 18px;
                font-weight: bold;
                color: {self.accent_color};
                margin-bottom: 15px;
            }}
            .quiz-title {{
                font-size: 18px;
                font-weight: bold;
                color: {self.accent_color};
                margin-bottom: 10px;
            }}
            .quiz-question {{
                font-size: 16px;
                margin-bottom: 15px;
                color: {self.text_dark};
            }}
            .quiz-progress {{
                font-size: 14px;
                color: {self.text_dark};
                margin-bottom: 10px;
            }}
            .welcome-message {{
                font-size: 24px;
                font-weight: bold;
                color: {self.accent_color};
                margin-bottom: 20px;
            }}
            .admin-welcome {{
                font-size: 24px;
                font-weight: bold;
                color: #E23E57;
                margin-bottom: 20px;
                text-align: center;
            }}
            .admin-desc {{
                font-size: 16px;
                color: #333333;
                margin-bottom: 30px;
                text-align: center;
            }}
        """
        )

        self.token = None
        self.is_admin = False
        self.api_entry_point = None
        self.categories = []
        self.quizzes = []
        self.questions = []

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Sidebar menu
        self.sidebar = QWidget()
        self.sidebar.setProperty("class", "sidebar")
        self.sidebar.setFixedWidth(220)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(0, 10, 0, 10)
        self.sidebar_layout.setSpacing(5)

        # App title and icon
        app_title = QLabel("QuizApp")
        app_title.setAlignment(Qt.AlignCenter)
        app_title.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: white; padding: 15px;"
        )

        # Mode indicator
        self.mode_label = QLabel("Hi User")
        self.mode_label.setAlignment(Qt.AlignCenter)
        self.mode_label.setStyleSheet("font-weight: bold; color: white;")

        # Menu buttons with icons
        self.menu_buttons = {
            "Browse Content": QPushButton(" Browse Content"),
            "Take a Quiz": QPushButton(" Take a Quiz"),
            "Admin Login": QPushButton(" Admin Login"),
            "Exit": QPushButton(" Exit"),
        }

        # Set icons for buttons
        try:
            self.menu_buttons["Browse Content"].setIcon(QIcon("icons/browse_icon.png"))
            self.menu_buttons["Take a Quiz"].setIcon(QIcon("icons/quiz_icon.png"))
            self.menu_buttons["Admin Login"].setIcon(QIcon("icons/admin_icon.png"))
            self.menu_buttons["Exit"].setIcon(QIcon("icons/exit_icon.png"))
        except:
            pass

        for button in self.menu_buttons.values():
            button.setProperty("flat", "true")
            button.setIconSize(QSize(24, 24))
            button.setStyleSheet(
                "text-align: left; padding: 12px 16px; font-size: 14px;"
            )
            button.setCursor(Qt.PointingHandCursor)

        # Add widgets to sidebar
        self.sidebar_layout.addWidget(app_title)
        self.sidebar_layout.addWidget(self.mode_label)
        self.sidebar_layout.addSpacing(10)

        for button in self.menu_buttons.values():
            self.sidebar_layout.addWidget(button)

        self.sidebar_layout.addStretch()

        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #555;")
        self.sidebar_layout.addWidget(separator)

        # Add version/copyright info
        version_label = QLabel("v1.0 © 2025 QuizApp")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #aaa; font-size: 10px; padding: 10px;")
        self.sidebar_layout.addWidget(version_label)

        # Main content area
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setStyleSheet(
            f"background-color: {self.light_cream}; padding: 20px;"
        )

        # Login page
        self.login_page = QWidget()
        self.setup_login_page()
        self.stacked_widget.addWidget(self.login_page)

        # Main menu page
        self.main_menu_page = QWidget()
        self.setup_main_menu_page()
        self.stacked_widget.addWidget(self.main_menu_page)

        # Browse content pages
        self.browse_content_page = QWidget()
        self.setup_browse_content_page()
        self.stacked_widget.addWidget(self.browse_content_page)

        # Quiz Page
        self.quiz_instructions_page = QWidget()
        self.setup_quiz_instructions_page()
        self.stacked_widget.addWidget(self.quiz_instructions_page)

        # Quiz flow pages
        self.quiz_flow_page = QWidget()
        self.setup_quiz_flow_page()
        self.stacked_widget.addWidget(self.quiz_flow_page)

        # Quiz Result page
        self.quiz_results_page = QWidget()
        self.setup_quiz_results_page()
        self.stacked_widget.addWidget(self.quiz_results_page)

        self.quiz_history = []

        # Admin management pages
        self.admin_manage_page = QWidget()
        self.setup_admin_manage_page()
        self.stacked_widget.addWidget(self.admin_manage_page)

        self.layout.addWidget(self.sidebar)
        self.layout.addWidget(self.stacked_widget)

        self.connect_signals()
        self.load_api_entry_point()
        QTimer.singleShot(100, self.load_initial_data)

        self.categories = self._get_categories()  # Load categories immediately
        self.quizzes = self._get_quizzes()  # Load quizzes
        self.questions = self._get_questions()  # Load questions
        self.show_main_menu()

    def load_initial_data(self):
        """Load all initial data from API"""
        try:
            self.categories = self._get_categories()
            self.quizzes = self._get_quizzes()
            self.questions = self._get_questions()
        except Exception as e:
            QMessageBox.warning(
                self, "Loading Error", f"Failed to load initial data: {str(e)}"
            )

    # Hypermedia methods
    def load_api_entry_point(self):
        """Load the API entry point to discover available resources"""
        try:
            response = requests.get(API_BASE_URL)
            if response.status_code == 200:
                self.api_entry_point = response.json()
            else:
                QMessageBox.critical(self, "Error", "Failed to connect to API")
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to connect to API: {str(e)}")

    def _get_link(self, resource, rel):
        """Get a hypermedia link from a resource"""
        if not resource or "_links" not in resource:
            return None
        return resource["_links"].get(rel)

    def _follow_link(self, link, method="GET", data=None):
        """Follow a hypermedia link with proper URL handling"""
        if not link:
            return None

        try:
            # Handle both string URLs and link objects
            url = link if isinstance(link, str) else link.get("href")
            if not url:
                return None

            # Ensure URL is absolute
            if not url.startswith("http"):
                if not url.startswith("/"):
                    url = "/" + url
                url = f"{API_BASE_URL}{url}"

            # Properly encode the URL (handles spaces and special chars)
            from urllib.parse import quote

            url = quote(url, safe="/:?=&")

            headers = {"Accept": "application/json"}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            response = requests.request(method, url, json=data, headers=headers)

            if response.status_code >= 400:
                self._handle_error(response)
                return None

            return response.json() if response.content else None

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to access {url}: {str(e)}")
            return None

    def _get_schema(self, rel_name):
        """Get schema for a resource"""
        link = self._get_link(self.api_entry_point, rel_name)
        if not link or not isinstance(link, dict):
            return None

        schema_url = link.get("schema")
        if not schema_url:
            return None

        if not schema_url.startswith("http"):
            schema_url = f"{API_BASE_URL}{schema_url}"

        try:
            response = requests.get(schema_url)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException:
            return None

        return None

    def _handle_error(self, response):
        """Show API error message in a dialog."""
        try:
            error_data = response.json()
            msg = error_data.get("msg", "Unknown error")
        except ValueError:
            msg = response.text or "Unknown error"

        QMessageBox.critical(self, f"Error {response.status_code}", msg)

    def setup_main_menu_page(self):
        """Create main menu page layout."""
        layout = QVBoxLayout(self.main_menu_page)
        layout.setAlignment(Qt.AlignCenter)

        self.welcome_label = QLabel("Welcome to QuizApp!")
        self.welcome_label.setProperty("class", "welcome-message")
        self.welcome_label.setAlignment(Qt.AlignCenter)

        self.desc_label = QLabel(
            "Test your knowledge with our interactive quizzes.\n"
            "Browse content or take a quiz to get started!"
        )
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setStyleSheet(
            """
            font-size: 16px; 
            color: black; 
            margin-bottom: 30px;
        """
        )

        layout.addWidget(self.welcome_label)
        layout.addWidget(self.desc_label)
        layout.addStretch()

    def setup_login_page(self):
        """Set up admin login form."""
        layout = QVBoxLayout(self.login_page)
        layout.setContentsMargins(100, 50, 100, 50)
        layout.setSpacing(20)

        title = QLabel("Admin Login")
        title.setProperty("class", "admin-title")
        title.setAlignment(Qt.AlignCenter)

        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        login_button = QPushButton("Login")
        login_button.setStyleSheet(f"background-color: {self.accent_color};")
        login_button.clicked.connect(self.handle_login)

        back_button = QPushButton("Back")
        back_button.setStyleSheet("background-color: #f44336;")
        back_button.clicked.connect(self.show_main_menu)

        button_layout = QHBoxLayout()
        button_layout.addWidget(login_button)
        button_layout.addWidget(back_button)

        form_layout.addWidget(QLabel("Username:"))
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(QLabel("Password:"))
        form_layout.addWidget(self.password_input)
        form_layout.addLayout(button_layout)

        layout.addWidget(title)
        layout.addLayout(form_layout)
        layout.addStretch()

    def setup_browse_content_page(self):
        """Initialize content browsing interface."""
        layout = QVBoxLayout(self.browse_content_page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Create a horizontal layout for the title and home button
        title_layout = QHBoxLayout()

        self.browse_title = QLabel()
        self.browse_title.setProperty("class", "content-title")
        title_layout.addWidget(self.browse_title)

        # Add home button with icon
        self.home_button = QPushButton()
        self.home_button.setIcon(
            QIcon("icons/home.png")
        )  # Make sure home.png is in your working directory
        self.home_button.setIconSize(QSize(28, 28))
        self.home_button.setFlat(True)
        self.home_button.setCursor(Qt.PointingHandCursor)
        self.home_button.clicked.connect(self.show_main_menu)
        title_layout.addWidget(self.home_button, 0, Qt.AlignRight)

        layout.addLayout(title_layout)

        self.content_table = QTableWidget()
        self.content_table.setColumnCount(3)
        self.content_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.content_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.content_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.content_table.setStyleSheet(
            """
            QTableWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """
        )

        self.detail_view = QTextEdit()
        self.detail_view.setReadOnly(True)
        self.detail_view.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
            }
        """
        )
        self.detail_view.hide()  # Hide it initially

        self.back_button = QPushButton("Back")
        self.back_button.setStyleSheet("background-color: #f44336;")
        self.back_button.clicked.connect(self.show_browse_content)
        self.back_button.hide()

        layout.addWidget(self.content_table, 1)
        layout.addWidget(self.detail_view, 1)  # Keep it in layout but hidden
        layout.addWidget(self.back_button, 0, Qt.AlignRight)

    def setup_quiz_instructions_page(self):
        """Create quiz instructions page."""

        layout = QVBoxLayout(self.quiz_instructions_page)
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(20)

        # Title
        title = QLabel("Quiz Instructions")
        title.setProperty("class", "content-title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Instructions
        instructions = QLabel(
            "Welcome to the Quiz!\n\n"
            "Here's how it works:\n\n"
            "1. You'll first select a category\n"
            "2. Then choose a quiz from that category\n"
            "3. Select your preferred difficulty level\n"
            "4. Choose how many questions you want\n"
            "5. Answer each question one at a time\n\n"
            "You'll see your score at the end. Good luck!"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("font-size: 14px; margin-bottom: 20px;")
        layout.addWidget(instructions)

        # Button layout
        button_layout = QHBoxLayout()

        back_button = QPushButton("Home")
        back_button.setStyleSheet("background-color: #f44336;")
        back_button.clicked.connect(self.show_main_menu)

        start_button = QPushButton("Start Quiz")
        start_button.setStyleSheet(f"background-color: {self.accent_color};")
        start_button.clicked.connect(self.start_quiz_after_instructions)

        button_layout.addWidget(back_button)
        button_layout.addWidget(start_button)

        layout.addLayout(button_layout)
        layout.addStretch()

    def start_quiz_after_instructions(self):
        """Continue with the original quiz flow after showing instructions"""
        if not self.categories:
            QMessageBox.warning(self, "Error", "No categories available")
            self.show_main_menu()
            return

        # Store quiz parameters for history
        self.current_quiz_params = {
            "category": None,
            "quiz": None,
            "difficulty": None,
            "question_count": None,
        }

        category, ok = QInputDialog.getItem(
            self,
            "Select Category",
            "Choose a category:",
            [cat["name"] for cat in self.categories],
            0,
            False,
        )

        if not ok:
            return

        self.current_quiz_params["category"] = category
        quizzes = self._get_quizzes_by_category(category)

        quizzes = self._get_quizzes_by_category(category)
        if not quizzes:
            QMessageBox.warning(self, "Error", f"No quizzes found in {category}")
            return

        quiz, ok = QInputDialog.getItem(
            self,
            "Select Quiz",
            "Choose a quiz:",
            [f"{q['name']} - {q['description']}" for q in quizzes],
            0,
            False,
        )

        if not ok:
            return

        quiz_id = quizzes[
            [f"{q['name']} - {q['description']}" for q in quizzes].index(quiz)
        ]["unique_id"]
        questions = self._get_questions_by_quiz(quiz_id)

        if not questions:
            QMessageBox.warning(self, "Error", "No questions found in this quiz")
            return

        complexity, ok = QInputDialog.getItem(
            self,
            "Select Complexity",
            "Choose complexity level:",
            ["easy", "medium", "hard", "all"],
            0,
            False,
        )

        if not ok:
            return

        if complexity != "all":
            questions = [q for q in questions if q["complex_level"] == complexity]
            if not questions:
                QMessageBox.warning(self, "Error", f"No {complexity} questions found")
                return

        count, ok = QInputDialog.getInt(
            self,
            "Number of Questions",
            f"Enter number of questions (1-{len(questions)}):",
            min(5, len(questions)),
            1,
            len(questions),
            1,
        )

        if not ok:
            return

        self.current_quiz = {
            "name": quiz.split(" - ")[0],
            "questions": questions[:count],
            "current_question": 0,
            "score": 0,
        }

        self.show_quiz_question()

    def view_quiz_history_details(self, item):
        """Show details of a historical quiz attempt"""
        index = self.history_list.row(item)
        attempt = self.quiz_history[
            -(index + 1)
        ]  # Reverse index since we display reversed

        details = QMessageBox()
        details.setWindowTitle("Quiz Attempt Details")
        details.setText(
            f"<h3>{attempt['quiz_name']}</h3>"
            f"<p>Date: {attempt['timestamp']}</p>"
            f"<p>Score: {attempt['score']}/{attempt['total']}</p>"
            f"<p>Percentage: {attempt['percentage']:.0f}%</p>"
        )
        details.setIcon(QMessageBox.Information)
        details.exec_()

    def setup_quiz_flow_page(self):
        """Prepare quiz question/answer interface."""
        layout = QVBoxLayout(self.quiz_flow_page)
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(20)

        self.quiz_title = QLabel()
        self.quiz_title.setProperty("class", "quiz-title")

        self.quiz_progress = QLabel()
        self.quiz_progress.setProperty("class", "quiz-progress")

        self.quiz_question = QLabel()
        self.quiz_question.setProperty("class", "quiz-question")
        self.quiz_question.setWordWrap(True)

        self.quiz_options = QButtonGroup()
        self.quiz_options_layout = QVBoxLayout()
        self.quiz_options_layout.setSpacing(10)

        submit_button = QPushButton("Submit Answer")
        submit_button.setStyleSheet(
            f"background-color: {self.accent_color}; font-size: 16px; padding: 10px;"
        )
        submit_button.clicked.connect(self.handle_quiz_answer)

        back_button = QPushButton("Cancel Quiz")
        back_button.setStyleSheet(
            "background-color: #f44336; font-size: 16px; padding: 10px;"
        )
        back_button.clicked.connect(self.show_main_menu)

        back_button = QPushButton("Cancel Quiz")
        back_button.setStyleSheet(
            "background-color: #f44336; font-size: 16px; padding: 10px;"
        )
        back_button.clicked.connect(self.cancel_quiz)

        options_widget = QWidget()
        options_widget.setLayout(self.quiz_options_layout)

        button_layout = QHBoxLayout()
        button_layout.addWidget(back_button)
        button_layout.addWidget(submit_button)

        layout.addWidget(self.quiz_title)
        layout.addWidget(self.quiz_progress)
        layout.addWidget(self.quiz_question)
        layout.addWidget(options_widget, 1)
        layout.addLayout(button_layout)

    def setup_admin_manage_page(self):
        """Set up admin management dashboard."""
        layout = QVBoxLayout(self.admin_manage_page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        self.admin_title = QLabel("Admin Management")
        self.admin_title.setProperty("class", "admin-title")

        self.admin_table = QTableWidget()
        self.admin_table.setColumnCount(3)
        self.admin_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.admin_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.admin_table.setEditTriggers(QTableWidget.NoEditTriggers)

        button_layout = QHBoxLayout()
        self.create_button = QPushButton("Create")
        self.update_button = QPushButton("Update")
        self.delete_button = QPushButton("Delete")

        self.create_button.setStyleSheet(f"background-color: #008000;")
        self.update_button.setStyleSheet("background-color: #2196F3;")
        self.delete_button.setStyleSheet("background-color: #f44336;")

        self.create_button.clicked.connect(lambda: None)
        self.update_button.clicked.connect(lambda: None)
        self.delete_button.clicked.connect(lambda: None)

        button_layout.addWidget(self.create_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.delete_button)

        back_button = QPushButton("Back")
        back_button.setStyleSheet("background-color: #f44336;")
        back_button.clicked.connect(self.show_admin_menu)

        layout.addWidget(self.admin_title)
        layout.addWidget(self.admin_table, 1)
        layout.addLayout(button_layout)
        layout.addWidget(back_button, 0, Qt.AlignRight)

    def connect_signals(self):
        """Connect UI signals to their handlers."""
        self.menu_buttons["Browse Content"].clicked.connect(self.show_browse_content)
        self.menu_buttons["Take a Quiz"].clicked.connect(self.handle_take_quiz)
        self.menu_buttons["Admin Login"].clicked.connect(self.show_login_page)
        self.menu_buttons["Exit"].clicked.connect(self.close)

    def handle_take_quiz(self):
        """Handle the Take a Quiz button click based on current state"""
        if hasattr(self, "current_quiz"):
            # Quiz is in progress, ask user what they want to do
            reply = QMessageBox.question(
                self,
                "Quiz in Progress",
                "You have a quiz in progress. What would you like to do?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Cancel,
            )

            if reply == QMessageBox.Yes:
                # Continue current quiz
                self.show_quiz_question()
            elif reply == QMessageBox.No:
                # Start new quiz (cancel current)
                if (
                    QMessageBox.question(
                        self,
                        "Confirm",
                        "Are you sure you want to start a new quiz? Current progress will be lost.",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    == QMessageBox.Yes
                ):
                    del self.current_quiz
                    self.start_quiz_flow()
        else:
            # No quiz in progress, start new one
            self.start_quiz_flow()

    def show_main_menu(self):
        """Switch to main menu view."""
        if self.is_admin:
            self.welcome_label.setText(
                "Welcome Admin! Manage your quizzes and questions"
            )
        else:
            self.welcome_label.setText("Welcome to QuizApp! Test your knowledge")
        self.stacked_widget.setCurrentWidget(self.main_menu_page)

    def show_login_page(self):
        """Display admin login screen."""
        self.username_input.clear()
        self.password_input.clear()
        self.stacked_widget.setCurrentWidget(self.login_page)

    def handle_login(self):
        """Authenticate admin credentials."""
        username = self.username_input.text()
        password = self.password_input.text()

        login_link = self._get_link(self.api_entry_point, "login")
        if not login_link:
            QMessageBox.warning(self, "Error", "Login endpoint not available")
            return

        response = self._follow_link(
            login_link, "POST", data={"username": username, "password": password}
        )

        if response and "access_token" in response:
            self.token = response["access_token"]
            self.is_admin = True
            self.mode_label.setText("ADMIN MODE")
            self.mode_label.setStyleSheet("font-weight: bold; color: white;")
            self.menu_buttons["Admin Login"].setText("Admin Tools")
            self.menu_buttons["Admin Login"].clicked.disconnect()
            self.menu_buttons["Admin Login"].clicked.connect(self.show_admin_menu)
            self.menu_buttons["Take a Quiz"].setVisible(False)

            self.desc_label.setText(
                "Manage quizzes, questions, and categories.\n"
                "Use the Admin Tools menu to get started!"
            )

            self.show_main_menu()
        else:
            QMessageBox.warning(self, "Error", "Invalid admin credentials")

    def show_browse_content(self):
        """Show content browsing page."""
        self.stacked_widget.setCurrentWidget(self.browse_content_page)
        self.show_browse_menu()

    def show_browse_menu(self):
        """Show top-level browse options."""
        self.browse_title.setText("Browse Content")
        self.content_table.clear()
        self.content_table.setRowCount(3)
        self.content_table.setColumnCount(1)
        self.content_table.setHorizontalHeaderLabels(["Options"])

        items = ["Categories", "Quizzes", "Questions"]
        for row, item in enumerate(items):
            self.content_table.setItem(row, 0, QTableWidgetItem(item))

        self.content_table.cellClicked.connect(self.handle_browse_selection)
        self.detail_view.hide()  # Hide the detail view
        self.detail_view.clear()
        self.back_button.hide()

    def handle_browse_selection(self, row, col):
        """Handle selection in browse table."""
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
        """Display all categories."""
        self.browse_title.setText("Categories")
        self.content_table.clear()
        self.content_table.setRowCount(len(self.categories))
        self.content_table.setColumnCount(1)
        self.content_table.setHorizontalHeaderLabels(["Category Name"])

        for row, category in enumerate(self.categories):
            self.content_table.setItem(row, 0, QTableWidgetItem(category["name"]))

        self.detail_view.show()
        self.detail_view.clear()
        self.back_button.show()

    def show_category_detail(self, category):
        """Show details for a single category."""
        # Encode the category name for URL
        from urllib.parse import quote

        encoded_name = quote(category["name"])

        category_link = self._get_link(category, "self")
        response = self._follow_link(category_link)

        if not response:
            return

        quizzes = self._get_quizzes_by_category(encoded_name)
        detail_text = (
            f"<h2>{response['name']}</h2>" f"<p>Contains {len(quizzes)} quizzes</p>"
        )

        if quizzes:
            detail_text += "<h3>Quizzes in this category:</h3><ul>"
            for quiz in quizzes:
                detail_text += f"<li>{quiz['name']} - {quiz['description']}</li>"
            detail_text += "</ul>"

        self.detail_view.setHtml(detail_text)

    def show_quizzes(self):
        """List all available quizzes."""
        self.browse_title.setText("Quizzes")
        self.content_table.clear()
        self.content_table.setRowCount(len(self.quizzes))
        self.content_table.setColumnCount(2)
        self.content_table.setHorizontalHeaderLabels(["Quiz Name", "Description"])

        for row, quiz in enumerate(self.quizzes):
            self.content_table.setItem(row, 0, QTableWidgetItem(quiz["name"]))
            self.content_table.setItem(
                row, 1, QTableWidgetItem(quiz.get("description", ""))
            )

        self.detail_view.show()
        self.detail_view.clear()
        self.back_button.show()

    def show_quiz_detail(self, quiz):
        """Display quiz details and questions."""
        quiz_link = self._get_link(quiz, "self")
        response = self._follow_link(quiz_link)

        if not response:
            return

        questions = self._get_questions_by_quiz(quiz["unique_id"])
        detail_text = (
            f"<h2>{response['name']}</h2>"
            f"<p><i>{response['description']}</i></p>"
            f"<p>Category: {response.get('category', 'N/A')}</p>"
            f"<p>Questions: {len(questions)}</p>"
        )

        if questions:
            detail_text += "<h3>Questions in this quiz:</h3><ul>"
            for question in questions:
                detail_text += (
                    f"<li>{question['question_statement']} "
                    f"({question['complex_level']})</li>"
                )
            detail_text += "</ul>"

        self.detail_view.setHtml(detail_text)

    def show_questions(self):
        """List all questions."""
        self.browse_title.setText("Questions")
        self.content_table.clear()
        self.content_table.setRowCount(len(self.questions))
        self.content_table.setColumnCount(4)
        self.content_table.setHorizontalHeaderLabels(
            ["Question", "Complexity", "Quiz", "Category"]
        )

        for row, question in enumerate(self.questions):
            self.content_table.setItem(
                row, 0, QTableWidgetItem(question["question_statement"])
            )
            self.content_table.setItem(
                row, 1, QTableWidgetItem(question["complex_level"])
            )

            quiz_info = "N/A"
            category_info = "N/A"
            if "quiz_unique_id" in question:
                quizzes = self._get_quizzes()
                quiz_resource = next(
                    (
                        q
                        for q in quizzes
                        if q["unique_id"] == question["quiz_unique_id"]
                    ),
                    None,
                )
                if quiz_resource:
                    quiz_link = self._get_link(quiz_resource, "self")
                    quiz = self._follow_link(quiz_link)

                if quiz:
                    quiz_info = quiz["name"]
                    if "category" in quiz:
                        category_info = quiz["category"]

            self.content_table.setItem(row, 2, QTableWidgetItem(quiz_info))
            self.content_table.setItem(row, 3, QTableWidgetItem(category_info))

        self.detail_view.show()
        self.detail_view.clear()
        self.back_button.show()

    def show_question_detail(self, question):
        """Show question details and options."""
        from urllib.parse import quote

        question_id = quote(question["unique_id"])

        question_link = self._get_link(question, "self")
        response = self._follow_link(question_link)

        if not response:
            return

        quiz_info = ""
        if "quiz_unique_id" in response:
            quiz = self._follow_link(f"/quiz/{response['quiz_unique_id']}")
            if quiz:
                quiz_info = f"<p>Quiz: {quiz['name']}</p>"
                if "category" in quiz:
                    quiz_info += f"<p>Category: {quiz['category']}</p>"

        options_text = "<h3>Options:</h3><ul>"
        for opt in response["options"]:
            if self.is_admin:
                options_text += (
                    f"<li>{opt['option_statement']} "
                    f"{'✓' if opt['is_correct'] else ''}</li>"
                )
            else:
                options_text += f"<li>{opt['option_statement']}</li>"
        options_text += "</ul>"

        detail_text = (
            f"<h2>{response['question_statement']}</h2>"
            f"<p>Complexity: {response['complex_level']}</p>"
            f"{quiz_info}"
            f"{options_text}"
        )

        self.detail_view.setHtml(detail_text)
        self.back_button.show()

    def _get_categories(self):
        """Fetch all categories from API."""
        categories_link = self._get_link(self.api_entry_point, "category")
        if not categories_link:
            QMessageBox.warning(self, "Error", "Categories endpoint not available")
            return []

        response = self._follow_link(categories_link)
        if not response:
            return []

        # Handle different possible response formats
        if isinstance(response, list):
            return response  # Direct array of categories
        elif "categories" in response:
            return response["categories"]  # Wrapped in 'categories' key
        elif "items" in response:
            return response["items"]  # Paginated response
        return []  # Fallback

    def _get_quizzes(self):
        """Retrieve all quizzes from API."""
        quizzes_link = self._get_link(self.api_entry_point, "quiz")
        if not quizzes_link:
            QMessageBox.warning(self, "Error", "Quizzes endpoint not available")
            return []

        response = self._follow_link(quizzes_link)
        return response.get("quizzes", []) if response else []

    def _get_questions(self):
        """Fetch all questions from API."""
        questions_link = self._get_link(self.api_entry_point, "question")
        if not questions_link:
            QMessageBox.warning(self, "Error", "Questions endpoint not available")
            return []

        response = self._follow_link(questions_link)
        return response.get("questions", []) if response else []

    def _get_quizzes_by_category(self, category_name):
        """
        Retrieves quizzes for a given category using hypermedia links.
        """
        # Get the list of categories (with _links)
        categories = self._get_categories()
        if not categories:
            QMessageBox.warning(self, "Error", "Failed to retrieve categories")
            return []

        # Find the category resource by name
        from urllib.parse import unquote

        decoded_name = unquote(category_name)

        category_resource = next(
            (
                c
                for c in categories
                if c.get("name", "").lower() == decoded_name.lower()
            ),
            None,
        )

        if not category_resource:
            QMessageBox.warning(self, "Error", f"Category '{category_name}' not found")
            return []

        # Follow the 'self' link to get the full category resource (with 'quizzes' link)
        category_self_link = self._get_link(category_resource, "self")
        if not category_self_link:
            QMessageBox.warning(self, "Error", "Category self link not available")
            return []

        category_detail = self._follow_link(category_self_link)
        if not category_detail:
            return []

        # Now get the 'quizzes' link from the full category resource
        quizzes_link = self._get_link(category_detail, "quizzes")
        if not quizzes_link:
            QMessageBox.warning(self, "Error", "Category quizzes link not available")
            return []

        # Follow the quizzes link to get quizzes
        response = self._follow_link(quizzes_link)
        return response.get("quizzes", []) if response else []

    def _get_questions_by_quiz(self, quiz_id):
        """
        Retrieves questions for a given quiz using hypermedia links.
        """
        # Get the list of quizzes (with _links)
        quizzes = self._get_quizzes()
        if not quizzes:
            QMessageBox.warning(self, "Error", "Failed to retrieve quizzes")
            return []

        # Find the quiz resource by ID
        quiz_resource = next(
            (q for q in quizzes if q.get("unique_id") == quiz_id), None
        )
        if not quiz_resource:
            QMessageBox.warning(self, "Error", f"Quiz with ID '{quiz_id}' not found")
            return []

        # Follow the 'self' link to get the full quiz resource (with 'questions' link)
        quiz_self_link = self._get_link(quiz_resource, "self")
        if not quiz_self_link:
            QMessageBox.warning(self, "Error", "Quiz self link not available")
            return []

        quiz_detail = self._follow_link(quiz_self_link)
        if not quiz_detail:
            return []

        # Now get the 'questions' link from the full quiz resource
        questions_link = self._get_link(quiz_detail, "questions")
        if not questions_link:
            QMessageBox.warning(self, "Error", "Quiz questions link not available")
            return []

        # Follow the questions link to get questions
        response = self._follow_link(questions_link)
        return response.get("questions", []) if response else []

    def start_quiz_flow(self):
        """Start a new quiz flow"""
        # Reset any current quiz state
        if hasattr(self, "current_quiz"):
            del self.current_quiz

        # Show instructions page
        self.stacked_widget.setCurrentWidget(self.quiz_instructions_page)

    def show_quiz_question(self):
        """Display current quiz question."""
        self.stacked_widget.setCurrentWidget(self.quiz_flow_page)

        question = self.current_quiz["questions"][self.current_quiz["current_question"]]
        question_link = self._get_link(question, "self")
        response = self._follow_link(question_link)
        if not response:
            return

        self.quiz_title.setText(f"Quiz: {self.current_quiz['name']}")
        self.quiz_progress.setText(
            f"Question {self.current_quiz['current_question'] + 1}/"
            f"{len(self.current_quiz['questions'])} | "
            f"Score: {self.current_quiz['score']}/{self.current_quiz['current_question']}"
        )

        self.quiz_question.setText(response["question_statement"])

        for i in reversed(range(self.quiz_options_layout.count())):
            self.quiz_options_layout.itemAt(i).widget().setParent(None)
        self.quiz_options = QButtonGroup()

        for i, opt in enumerate(response["options"]):
            radio = QRadioButton(opt["option_statement"])
            self.quiz_options.addButton(radio, i)
            self.quiz_options_layout.addWidget(radio)

    def handle_quiz_answer(self):
        """Validate answer and update score."""
        if not self.quiz_options.checkedButton():
            QMessageBox.warning(self, "Error", "Please select an answer")
            return

        question = self.current_quiz["questions"][self.current_quiz["current_question"]]
        question_link = self._get_link(question, "self")
        response = self._follow_link(question_link)

        if not response:
            return

        selected_index = self.quiz_options.checkedId()
        if response["options"][selected_index]["is_correct"]:
            self.current_quiz["score"] += 1
            QMessageBox.information(self, "Correct", "✓ Correct answer!")
        else:
            correct_index = next(
                i for i, opt in enumerate(response["options"]) if opt["is_correct"]
            )
            QMessageBox.warning(
                self,
                "Incorrect",
                f"✗ Incorrect! The correct answer was: "
                f"{response['options'][correct_index]['option_statement']}",
            )

        self.current_quiz["current_question"] += 1

        if self.current_quiz["current_question"] < len(self.current_quiz["questions"]):
            self.show_quiz_question()
        else:
            self.show_quiz_results()

    def setup_quiz_results_page(self):
        """Configure quiz results display."""
        layout = QVBoxLayout(self.quiz_results_page)
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(20)

        # Title
        self.results_title = QLabel("Quiz Results")
        self.results_title.setProperty("class", "content-title")
        self.results_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.results_title)

        # Results display
        self.results_display = QTextEdit()
        self.results_display.setReadOnly(True)
        self.results_display.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
            }
        """
        )
        layout.addWidget(self.results_display, 1)

        # History label
        self.history_label = QLabel("Your Attempts:")
        layout.addWidget(self.history_label)

        # History list
        self.history_list = QListWidget()
        self.history_list.setStyleSheet(
            """
            QListWidget {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 5px;
            }
        """
        )
        layout.addWidget(self.history_list, 1)
        self.history_list.itemClicked.connect(self.view_quiz_history_details)

        # Back button
        back_button = QPushButton("Back to Quiz Instructions")
        back_button.setStyleSheet(
            "background-color: #f44336; font-size: 16px; padding: 10px;"
        )
        back_button.clicked.connect(
            lambda: self.stacked_widget.setCurrentWidget(self.quiz_instructions_page)
        )
        layout.addWidget(back_button, 0, Qt.AlignRight)

    def show_quiz_results(self):
        """Calculate and display quiz results."""
        # Calculate results
        percentage = (
            self.current_quiz["score"] / len(self.current_quiz["questions"])
        ) * 100
        if percentage >= 70:
            message = "Excellent!"
            color = "green"
        elif percentage >= 50:
            message = "Good effort!"
            color = "orange"
        else:
            message = "Keep practicing!"
            color = "red"

        # Create result text
        result_text = (
            f"<h2>Quiz: {self.current_quiz['name']}</h2>"
            f"<p>Correct Answers: <b>{self.current_quiz['score']}/"
            f"{len(self.current_quiz['questions'])}</b></p>"
            f"<p>Percentage: <b style='color:{color}'>{percentage:.0f}%</b></p>"
            f"<p>{message}</p>"
        )

        # Add to history
        history_entry = {
            "quiz_name": self.current_quiz["name"],
            "score": self.current_quiz["score"],
            "total": len(self.current_quiz["questions"]),
            "percentage": percentage,
            "timestamp": QDateTime.currentDateTime().toString("yyyy-MM-dd hh:mm"),
        }
        self.quiz_history.append(history_entry)

        # Update results display
        self.results_display.setHtml(result_text)

        # Update history list
        self.history_list.clear()
        for attempt in reversed(self.quiz_history):
            item = QListWidgetItem(
                f"{attempt['timestamp']} - {attempt['quiz_name']}: "
                f"{attempt['score']}/{attempt['total']} ({attempt['percentage']:.0f}%)"
            )
            self.history_list.addItem(item)

        # Show results page
        if hasattr(self, "current_quiz"):
            del self.current_quiz

        self.stacked_widget.setCurrentWidget(self.quiz_results_page)

        # Enable the Take a Quiz button in sidebar
        self.menu_buttons["Take a Quiz"].setEnabled(True)

    def cancel_quiz(self):
        """Handle quiz cancellation"""
        if hasattr(self, "current_quiz"):
            if (
                QMessageBox.question(
                    self,
                    "Cancel Quiz",
                    "Are you sure you want to cancel the current quiz?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                == QMessageBox.Yes
            ):
                del self.current_quiz
                self.stacked_widget.setCurrentWidget(self.quiz_instructions_page)

    def show_admin_menu(self):
        """Display admin management options."""
        if not self.is_admin:
            QMessageBox.warning(self, "Error", "Admin privileges required")
            if (
                QMessageBox.question(
                    self,
                    "Login",
                    "Do you want to login as admin now?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                == QMessageBox.Yes
            ):
                self.show_login_page()
            return

        self.stacked_widget.setCurrentWidget(self.admin_manage_page)
        self.show_admin_manage_menu()

    def show_admin_manage_menu(self):
        """Display admin management menu."""
        self.admin_title.setText("Admin Management")
        self.admin_table.clear()
        self.admin_table.setRowCount(4)
        self.admin_table.setColumnCount(1)
        self.admin_table.setHorizontalHeaderLabels(["Options"])

        items = ["Manage Categories", "Manage Quizzes", "Manage Questions", "Logout"]
        for row, item in enumerate(items):
            self.admin_table.setItem(row, 0, QTableWidgetItem(item))

        # Hide the CRUD buttons initially
        self.create_button.hide()
        self.update_button.hide()
        self.delete_button.hide()

        self.admin_table.cellClicked.connect(self.handle_admin_menu_selection)

    def handle_admin_menu_selection(self, row, col):
        """Handle admin management menu."""
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
        """Show category management view."""
        self.admin_title.setText("Category Management")
        self.admin_table.clear()
        self.admin_table.setRowCount(len(self.categories))
        self.admin_table.setColumnCount(1)
        self.admin_table.setHorizontalHeaderLabels(["Category Name"])

        for row, category in enumerate(self.categories):
            self.admin_table.setItem(row, 0, QTableWidgetItem(category["name"]))
            self.admin_table.item(row, 0).setData(Qt.UserRole, category)

        # Show the CRUD buttons for categories
        self.create_button.show()
        self.update_button.show()
        self.delete_button.show()

        # Remove any existing navigation connections
        try:
            self.admin_table.cellClicked.disconnect()
        except:
            pass

        # Connect new handlers without navigation
        self.admin_table.cellClicked.connect(self.handle_category_selection_without_nav)

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

    def handle_category_selection_without_nav(self, row, col):
        """ " Handle category selection without navigation"""
        # Just select the item without any navigation
        self.admin_table.selectRow(row)

    def create_category(self):
        """Add new category via dialog."""
        name, ok = QInputDialog.getText(self, "Create Category", "Enter category name:")
        if ok and name:
            response = self._follow_link(
                self._get_link(self.api_entry_point, "category"),
                "POST",
                data={"name": name},  # Make sure this matches exactly what API expects
            )
            if response and response.get("msg") == "Category created":
                QMessageBox.information(
                    self, "Success", "Category created successfully!"
                )
                self.categories = self._get_categories()
                self.manage_categories()
            else:
                error_msg = (
                    response.get("msg", "Unknown error")
                    if response
                    else "No response from server"
                )
                QMessageBox.warning(
                    self, "Error", f"Failed to create category: {error_msg}"
                )

    def update_category(self):
        """Modify selected category."""
        selected_row = self.admin_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a category to update")
            return

        category = self.admin_table.item(selected_row, 0).data(Qt.UserRole)
        new_name, ok = QInputDialog.getText(
            self, "Update Category", "Enter new category name:", text=category["name"]
        )

        if ok and new_name:

            category_link = self._get_link(category, "self")
            response = self._follow_link(category_link, "PUT", data={"name": new_name})

            if response and response.get("msg") == "Category updated":
                QMessageBox.information(
                    self, "Success", "Category updated successfully!"
                )
                self.categories = self._get_categories()
                self.manage_categories()
            else:
                QMessageBox.warning(self, "Error", "Failed to update category")

    def delete_category(self):
        """Delete selected category."""

        selected_row = self.admin_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a category to delete")
            return

        category = self.admin_table.item(selected_row, 0).data(Qt.UserRole)

        # First, get all quizzes in this category
        quizzes = self._get_quizzes_by_category(category["name"])

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{category['name']}' and all its "
            f"{len(quizzes)} quizzes?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            # First delete all quizzes in this category (which will cascade to questions)
            for quiz in quizzes:
                quiz_link = self._get_link(quiz, "self")
                response = self._follow_link(quiz_link, "DELETE")

                if not response or response.get("msg") != "Quiz deleted":
                    QMessageBox.warning(
                        self, "Error", f"Failed to delete quiz: {quiz['name']}"
                    )
                    return

            # Now delete the category itself
            category_link = self._get_link(category, "self")
            response = self._follow_link(category_link, "DELETE")

            if response and response.get("msg") == "Category deleted":
                QMessageBox.information(
                    self,
                    "Success",
                    f"Category and {len(quizzes)} quizzes deleted successfully!",
                )
                self.categories = self._get_categories()
                self.quizzes = self._get_quizzes()  # Refresh quizzes list
                self.questions = self._get_questions()  # Refresh questions list
                self.manage_categories()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete category")

    def manage_quizzes(self):
        """Show quiz management view."""
        self.admin_title.setText("Quiz Management")
        self.admin_table.clear()
        self.admin_table.setRowCount(len(self.quizzes))
        self.admin_table.setColumnCount(2)
        self.admin_table.setHorizontalHeaderLabels(["Quiz Name", "Description"])

        for row, quiz in enumerate(self.quizzes):
            self.admin_table.setItem(row, 0, QTableWidgetItem(quiz["name"]))
            self.admin_table.setItem(
                row, 1, QTableWidgetItem(quiz.get("description", ""))
            )
            self.admin_table.item(row, 0).setData(Qt.UserRole, quiz)

        # Show the CRUD buttons for quizzes
        self.create_button.show()
        self.update_button.show()
        self.delete_button.show()

        # Remove any existing navigation connections
        try:
            self.admin_table.cellClicked.disconnect()
        except:
            pass

        # Connect new handlers without navigation
        self.admin_table.cellClicked.connect(self.handle_quiz_selection_without_nav)

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

    def handle_quiz_selection_without_nav(self, row, col):
        """Handle quiz selection without navigation."""
        # Just select the item without any navigation
        self.admin_table.selectRow(row)

    def create_quiz(self):
        """Add new quiz via dialog."""
        # Get all required fields
        name, ok = QInputDialog.getText(self, "Create Quiz", "Enter quiz name:")
        if not ok or not name:
            return

        description, ok = QInputDialog.getText(
            self, "Create Quiz", "Enter quiz description:"
        )
        if not ok:
            return

        category, ok = QInputDialog.getItem(
            self,
            "Select Category",
            "Choose a category:",
            [cat["name"] for cat in self.categories],
            0,
            False,
        )
        if not ok:
            return

        # Send properly formatted request
        response = self._follow_link(
            self._get_link(self.api_entry_point, "quiz"),
            "POST",
            data={
                "name": name,
                "description": description,
                "category_name": category,  # Must match an existing category
            },
        )

        if response and response.get("msg") == "Quiz created":
            QMessageBox.information(self, "Success", "Quiz created successfully!")
            self.quizzes = self._get_quizzes()
            self.manage_quizzes()
        else:
            error_msg = (
                response.get("msg", "Unknown error")
                if response
                else "No response from server"
            )
            QMessageBox.warning(self, "Error", f"Failed to create quiz: {error_msg}")

    def update_quiz(self):
        """Edit selected quiz details."""
        selected_row = self.admin_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a quiz to update")
            return

        quiz = self.admin_table.item(selected_row, 0).data(Qt.UserRole)

        # Get current values
        current_name = quiz["name"]
        current_description = quiz.get("description", "")
        current_category = quiz.get("category", "")

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
        category_combo.addItems([cat["name"] for cat in self.categories])
        if current_category in [cat["name"] for cat in self.categories]:
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

            quiz_link = self._get_link(quiz, "self")
            response = self._follow_link(
                quiz_link,
                "PUT",
                data={
                    "name": name,
                    "description": description,
                    "category_name": category,
                },
            )

            if response and response.get("msg") == "Quiz updated":
                QMessageBox.information(self, "Success", "Quiz updated successfully!")
                self.quizzes = self._get_quizzes()
                self.manage_quizzes()
            else:
                QMessageBox.warning(self, "Error", "Failed to update quiz")

    def delete_quiz(self):
        """Remove quiz and its questions."""
        selected_row = self.admin_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a quiz to delete")
            return

        quiz = self.admin_table.item(selected_row, 0).data(Qt.UserRole)

        # Get all questions for this quiz
        questions = self._get_questions_by_quiz(quiz["unique_id"])

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{quiz['name']}' and its {len(questions)} questions?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:
            quiz_link = self._get_link(quiz, "self")
            response = self._follow_link(quiz_link, "DELETE")

            if response and response.get("msg") == "Quiz deleted":
                QMessageBox.information(
                    self,
                    "Success",
                    f"Quiz and {len(questions)} questions deleted successfully!",
                )
                self.quizzes = self._get_quizzes()
                self.questions = self._get_questions()  # Refresh questions list too
                self.manage_quizzes()
            else:
                error_msg = (
                    response.get("msg", "Unknown error")
                    if response
                    else "No response from server"
                )
                QMessageBox.warning(
                    self, "Error", f"Failed to delete quiz: {error_msg}"
                )

    def manage_questions(self):
        """Show question management view."""
        self.admin_title.setText("Question Management")
        self.admin_table.clear()
        self.admin_table.setRowCount(len(self.questions))
        self.admin_table.setColumnCount(2)
        self.admin_table.setHorizontalHeaderLabels(["Question", "Complexity"])

        for row, question in enumerate(self.questions):
            self.admin_table.setItem(
                row, 0, QTableWidgetItem(question["question_statement"])
            )
            self.admin_table.setItem(
                row, 1, QTableWidgetItem(question["complex_level"])
            )
            self.admin_table.item(row, 0).setData(Qt.UserRole, question)

        self.create_button.show()
        self.update_button.show()
        self.delete_button.show()

        # Remove any existing navigation connections
        try:
            self.admin_table.cellClicked.disconnect()
        except:
            pass

        # Connect new handlers without navigation
        self.admin_table.cellClicked.connect(self.handle_question_selection_without_nav)

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

    def handle_question_selection_without_nav(self, row, col):
        """Handle question selection without navigation."""
        # Just select the item without any navigation
        self.admin_table.selectRow(row)

    def create_question(self):
        """Add new question with options."""
        # Get basic question info
        statement, ok = QInputDialog.getText(
            self, "Create Question", "Enter question statement:"
        )
        if not ok or not statement:
            return

        complexity, ok = QInputDialog.getItem(
            self,
            "Select Complexity",
            "Choose complexity level:",
            ["easy", "medium", "hard"],
            0,
            False,
        )
        if not ok:
            return

        # Select quiz
        quiz, ok = QInputDialog.getItem(
            self,
            "Select Quiz",
            "Choose a quiz:",
            [f"{q['name']} (ID: {q['unique_id']})" for q in self.quizzes],
            0,
            False,
        )
        if not ok:
            return

        # Extract quiz ID from selection
        quiz_id = self.quizzes[
            [f"{q['name']} (ID: {q['unique_id']})" for q in self.quizzes].index(quiz)
        ]["unique_id"]

        # Create a dialog for options with 4 options by default
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Options (Select one correct answer)")
        layout = QVBoxLayout()

        options = []
        option_widgets = []
        options_group = QButtonGroup()  # To manage radio buttons

        # Add 4 options by default
        for i in range(4):
            hbox = QHBoxLayout()
            radio = QRadioButton()
            if i == 0:  # First option is correct by default
                radio.setChecked(True)
            options_group.addButton(radio, i)
            text_input = QLineEdit()
            text_input.setPlaceholderText(f"Option {i+1} text")
            hbox.addWidget(radio)
            hbox.addWidget(text_input)
            option_widgets.append((radio, text_input))
            layout.addLayout(hbox)

        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)

        if dialog.exec_() == QDialog.Accepted:
            # Prepare options data
            options = []
            for radio, text_input in option_widgets:
                if not text_input.text().strip():
                    QMessageBox.warning(self, "Error", "Option text cannot be empty")
                    return

                options.append(
                    {
                        "option_statement": text_input.text().strip(),
                        "is_correct": radio.isChecked(),
                    }
                )

            # Ensure exactly one correct option
            correct_count = sum(1 for opt in options if opt["is_correct"])
            if correct_count != 1:
                QMessageBox.warning(
                    self, "Error", "Exactly one option must be marked as correct"
                )
                return

            # Create the question
            response = self._follow_link(
                self._get_link(self.api_entry_point, "question"),
                "POST",
                data={
                    "question_statement": statement,
                    "complex_level": complexity,
                    "quiz_unique_id": quiz_id,
                    "options": options,
                },
            )

            if response and response.get("msg") == "Question created":
                QMessageBox.information(
                    self, "Success", "Question created successfully!"
                )
                self.questions = self._get_questions()
                self.manage_questions()
            else:
                error_msg = (
                    response.get("msg", "Unknown error")
                    if response
                    else "No response from server"
                )
                QMessageBox.warning(
                    self, "Error", f"Failed to create question: {error_msg}"
                )

    def update_question(self):
        """Modify question and options."""
        selected_row = self.admin_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a question to update")
            return

        question = self.admin_table.item(selected_row, 0).data(Qt.UserRole)

        # Get full question details from API
        question_link = self._get_link(question, "self")
        response = self._follow_link(question_link)

        if not response:
            QMessageBox.warning(self, "Error", "Failed to load question details")
            return

        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Update Question")
        dialog.setMinimumWidth(600)
        layout = QVBoxLayout(dialog)

        # Question statement
        stmt_label = QLabel("Question:")
        stmt_input = QTextEdit(response["question_statement"])
        layout.addWidget(stmt_label)
        layout.addWidget(stmt_input)

        # Complexity
        complex_label = QLabel("Complexity:")
        complex_combo = QComboBox()
        complex_combo.addItems(["easy", "medium", "hard"])
        complex_combo.setCurrentText(response["complex_level"])
        layout.addWidget(complex_label)
        layout.addWidget(complex_combo)

        # Quiz selection
        quiz_label = QLabel("Quiz:")
        quiz_combo = QComboBox()
        quiz_combo.addItems(
            [f"{q['name']} (ID: {q['unique_id']})" for q in self.quizzes]
        )

        # Set current quiz if available
        if "quiz_unique_id" in response:
            try:
                idx = [q["unique_id"] for q in self.quizzes].index(
                    response["quiz_unique_id"]
                )
                quiz_combo.setCurrentIndex(idx)
            except ValueError:
                pass

        layout.addWidget(quiz_label)
        layout.addWidget(quiz_combo)

        # Options
        options_label = QLabel("Options (Select one correct answer):")
        layout.addWidget(options_label)

        options_group = QButtonGroup()
        options_layout = QVBoxLayout()

        # Get current options
        options = response.get("options", [])

        # Ensure we have exactly 4 options (add empty ones if needed)
        while len(options) < 4:
            options.append({"option_statement": "", "is_correct": False})

        # Add option inputs (4 options)
        option_widgets = []
        for i, opt in enumerate(options[:4]):  # Only show first 4 options
            hbox = QHBoxLayout()
            radio = QRadioButton()
            radio.setChecked(opt["is_correct"])
            options_group.addButton(radio, i)
            text_input = QLineEdit(opt["option_statement"])
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
                if not text_input.text().strip():
                    QMessageBox.warning(self, "Error", "Option text cannot be empty")
                    return

                updated_options.append(
                    {
                        "option_statement": text_input.text().strip(),
                        "is_correct": radio.isChecked(),
                    }
                )

            # Ensure exactly one correct option
            correct_count = sum(1 for opt in updated_options if opt["is_correct"])
            if correct_count != 1:
                QMessageBox.warning(
                    self, "Error", "Exactly one option must be marked as correct"
                )
                return

            # Get selected quiz ID
            selected_quiz = quiz_combo.currentText()
            quiz_id = self.quizzes[
                [f"{q['name']} (ID: {q['unique_id']})" for q in self.quizzes].index(
                    selected_quiz
                )
            ]["unique_id"]

            update_data = {
                "question_statement": stmt_input.toPlainText().strip(),
                "complex_level": complex_combo.currentText(),
                "quiz_unique_id": quiz_id,
                "options": updated_options,
            }

            # Validate required fields
            if not update_data["question_statement"]:
                QMessageBox.warning(self, "Error", "Question statement cannot be empty")
                return

            question_link = self._get_link(question, "self")
            response = self._follow_link(question_link, "PUT", data=update_data)

            if response and response.get("msg") == "Question updated":
                QMessageBox.information(
                    self, "Success", "Question updated successfully!"
                )
                self.questions = self._get_questions()
                self.manage_questions()
            else:
                error_msg = (
                    response.get("msg", "Unknown error")
                    if response
                    else "No response from server"
                )
                QMessageBox.warning(
                    self, "Error", f"Failed to update question: {error_msg}"
                )

    def delete_question(self):
        """Remove selected question."""
        selected_row = self.admin_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Error", "Please select a question to delete")
            return

        question = self.admin_table.item(selected_row, 0).data(Qt.UserRole)

        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete this question?\n\n{question['question_statement']}",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm == QMessageBox.Yes:

            question_link = self._get_link(question, "self")
            response = self._follow_link(question_link, "DELETE")

            if (
                response
                and response.get("msg") == "Question and related records deleted"
            ):
                QMessageBox.information(
                    self, "Success", "Question deleted successfully!"
                )
                self.questions = self._get_questions()  # Refresh the list
                self.manage_questions()
            else:
                error_msg = (
                    response.get("msg", "Unknown error")
                    if response
                    else "No response from server"
                )
                QMessageBox.warning(
                    self, "Error", f"Failed to delete question: {error_msg}"
                )

    def logout(self):
        """End admin session and return to user mode."""
        self.token = None
        self.is_admin = False
        self.mode_label.setText("USER MODE")
        self.mode_label.setStyleSheet("font-weight: bold; color: orange;")
        self.menu_buttons["Admin Login"].setText("Admin Login")
        self.menu_buttons["Admin Login"].clicked.disconnect()
        self.menu_buttons["Admin Login"].clicked.connect(self.show_login_page)
        self.menu_buttons["Take a Quiz"].setVisible(True)

        # Hide CRUD buttons when logging out
        self.create_button.hide()
        self.update_button.hide()
        self.delete_button.hide()

        # Reset description text
        self.desc_label.setText(
            "Test your knowledge with our interactive quizzes.\n"
            "Browse content or take a quiz to get started!"
        )

        self.show_main_menu()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    client = QuizClientGUI()
    client.show()
    sys.exit(app.exec_())
