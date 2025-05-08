#!/usr/bin/env python3
"""
Complete Quiz API Client with Full Admin/User Separation and CRUD Operations

Features:
- Clear separation between admin and user interfaces
- Full CRUD operations for admin (Create, Read, Update, Delete)
- No quiz-taking for admin users
- Proper PUT/update functionality for all resources
- Clean interface with rich library
"""

import os
import json
import argparse
from getpass import getpass
import requests
from requests.exceptions import RequestException
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.style import Style
from rich.text import Text

# Configuration
API_BASE_URL = "http://127.0.0.1:5000"  # Default API URL
ADMIN_USERNAME = "admin"  # Default admin username
console = Console()

class QuizClient:
    """Main client class with separated admin/user functionality and full CRUD operations."""
    
    def __init__(self, base_url=API_BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
        self.is_admin = False
        self.categories = []
        self.quizzes = []
        self.questions = []
        
    def _get_headers(self):
        """Get headers with auth token if available."""
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def _make_request(self, method, endpoint, data=None, params=None):
        """Make an HTTP request and handle responses."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(
                method,
                url,
                json=data,
                params=params,
                headers=self._get_headers()
            )
            
            if response.status_code >= 400:
                self._handle_error(response)
                
            return response
            
        except RequestException as e:
            console.print(f"[red]Network error: {str(e)}[/red]")
            return None
    
    def _handle_error(self, response):
        """Handle API error responses."""
        try:
            error_data = response.json()
            msg = error_data.get('msg', 'Unknown error')
        except ValueError:
            msg = response.text or 'Unknown error'
            
        console.print(f"[red]Error {response.status_code}: {msg}[/red]")
        return None
    
    def _display_table(self, title, items, columns, show_index=False):
        """Display data in a rich table with optional index column."""
        table = Table(title=title, show_header=True, header_style="bold magenta")
        
        if show_index:
            table.add_column("#", style="dim")
        
        for col in columns:
            table.add_column(col)
            
        for i, item in enumerate(items, 1):
            row = [str(i)] if show_index else []
            row.extend(str(item.get(col, '')) for col in columns)
            table.add_row(*row)
            
        console.print(table)
    
    def _prompt_selection(self, items, prompt_text, display_field="name"):
        """Prompt user to select from a list of items."""
        if not items:
            console.print("[red]No items available[/red]")
            return None
            
        for i, item in enumerate(items, 1):
            console.print(f"{i}. {item.get(display_field)}")
            
        while True:
            try:
                choice = Prompt.ask(prompt_text)
                if choice.lower() == '0' or choice.lower() == 'exit':
                    return None
                index = int(choice) - 1
                if 0 <= index < len(items):
                    return items[index]
                console.print("[red]Invalid selection[/red]")
            except ValueError:
                console.print("[red]Please enter a number[/red]")
    
    def login(self, username=None, password=None):
        """Authenticate as admin."""
        console.print(Panel.fit("Admin Login", style="bold blue"))
        
        if username is None:
            username = Prompt.ask("Username")
        if password is None:
            password = getpass("Password: ")
            
        data = {
            "username": username,
            "password": password
        }
        
        response = self._make_request("POST", "/login", data=data)
        if response and response.status_code == 200:
            self.token = response.json().get('access_token')
            self.is_admin = True
            console.print("[green]Admin login successful![/green]")
            return True
        console.print("[red]Invalid admin credentials[/red]")
        return False
    
    def ensure_admin(self):
        """Check if admin, prompt login if not."""
        if self.is_admin:
            return True
            
        console.print("[yellow]Admin privileges required[/yellow]")
        if Confirm.ask("Do you want to login as admin now?"):
            return self.login()
        return False
    
    def load_resources(self):
        """Load all resources for navigation."""
        with console.status("[bold green]Loading resources...[/bold green]"):
            self.categories = self._get_categories()
            self.quizzes = self._get_quizzes()
            self.questions = self._get_questions()
    
    def _get_categories(self):
        """Get all categories."""
        response = self._make_request("GET", "/category")
        if response:
            data = response.json()
            return data.get('categories', [])
        return []
    
    def _get_quizzes(self):
        """Get all quizzes."""
        response = self._make_request("GET", "/quiz")
        if response:
            data = response.json()
            return data.get('quizzes', [])
        return []
    
    def _get_questions(self):
        """Get all questions."""
        response = self._make_request("GET", "/question")
        if response:
            data = response.json()
            return data.get('questions', [])
        return []
    
    def _get_quizzes_by_category(self, category_name):
        """Get quizzes for a specific category."""
        response = self._make_request("GET", f"/category/{category_name}/quizzes")
        if response:
            data = response.json()
            return data.get('quizzes', [])
        return []
    
    def _get_questions_by_quiz(self, quiz_id):
        """Get questions for a specific quiz."""
        response = self._make_request("GET", f"/quiz/{quiz_id}/questions")
        if response:
            data = response.json()
            return data.get('questions', [])
        return []
    
    def show_main_menu(self):
        """Display the appropriate menu based on user/admin status."""
        while True:
            console.print(Panel.fit(
                "[bold]Quiz API Client[/bold]",
                subtitle=f"{'[green]ADMIN MODE[/green]' if self.is_admin else '[yellow]USER MODE[/yellow]'}",
                style="bold blue"
            ))
            
            options = [
                ("Browse Content", self.browse_content_menu),
                ("Take a Quiz", self.start_quiz_flow),
                ("Admin Tools" if self.is_admin else "Admin Login", 
                 self._show_admin_menu if self.is_admin else self.login),
                ("Exit", None)
            ]
            if self.is_admin:

                options.pop(1)  # Remove the "Take a Quiz" option
                
            for i, (text, _) in enumerate(options, 1):
                console.print(f"{i}. {text}")
            
            try:
                choice = IntPrompt.ask("Select an option", choices=[str(i) for i in range(1, len(options)+1)])
                
                if choice == len(options):  # Exit
                    break
                    
                # Call the selected function
                result = options[choice-1][1]()
                if result is False:  # Login failed
                    continue
                    
            except ValueError:
                console.print("[red]Please enter a valid number[/red]")
    
    def _show_admin_menu(self):
        """Display the admin menu - no quiz taking option."""
        while True:
            console.print(Panel.fit("[bold]Admin Management[/bold]", style="bold blue"))
            
            options = [
                ("Manage Categories", self._manage_categories),
                ("Manage Quizzes", self._manage_quizzes),
                ("Manage Questions", self._manage_questions),
                ("Logout", self.logout),
                ("Back to Main Menu", None)
            ]
            
            for i, (text, _) in enumerate(options, 1):
                console.print(f"{i}. {text}")
            
            try:
                choice = IntPrompt.ask("Select an option", choices=[str(i) for i in range(1, len(options)+1)])
                
                if choice == len(options):  # Back to Main Menu
                    break
                    
                # Call the selected function
                result = options[choice-1][1]()
                if result is False:  # Something failed
                    continue
                    
            except ValueError:
                console.print("[red]Please enter a valid number[/red]")
    
    def logout(self):
        """Log out the admin user."""
        self.token = None
        self.is_admin = False
        console.print("[green]Successfully logged out[/green]")
        return True
    
    def browse_content_menu(self):
        """Menu for browsing categories, quizzes, and questions."""
        while True:
            console.print(Panel.fit("[bold]Browse Content[/bold]", style="blue"))
            console.print("1. Categories")
            console.print("2. Quizzes")
            console.print("3. Questions")
            console.print("0. Back to Main Menu")
            
            choice = Prompt.ask("Select content to browse", choices=["0", "1", "2", "3"])
            
            if choice == "0":
                break
            elif choice == "1":
                self._browse_categories()
            elif choice == "2":
                self._browse_quizzes()
            elif choice == "3":
                self._browse_questions()
    
    def _browse_categories(self):
        """Drill-down: Show categories → quizzes → questions → question details."""
        if not self.categories:
            console.print("[yellow]No categories found[/yellow]")
            return

        self._display_table(
            "Available Categories",
            self.categories,
            ["name"],
            show_index=True
        )

        while True:
            choice = Prompt.ask(
                "Enter category number to view quizzes (0 to go back)",
                choices=[str(i) for i in range(0, len(self.categories)+1)]
            )

            if choice == "0":
                break

            try:
                category = self.categories[int(choice)-1]
                self._show_category_detail(category)
            except (IndexError, ValueError):
                console.print("[red]Invalid selection[/red]")

    
    def _show_category_detail(self, category):
        """Show quizzes in the selected category."""
        quizzes = self._get_quizzes_by_category(category['name'])

        console.print(Panel.fit(
            f"[bold]{category['name']}[/bold]\n"
            f"[dim]Contains {len(quizzes)} quizzes[/dim]",
            style="blue"
        ))

        if quizzes:
            self._display_table(
                f"Quizzes in {category['name']}",
                quizzes,
                ["name", "description"],
                show_index=True
            )

            while True:
                choice = Prompt.ask(
                    f"Enter quiz number to view questions (0 to go back)",
                    choices=[str(i) for i in range(0, len(quizzes)+1)]
                )

                if choice == "0":
                    break

                try:
                    quiz = quizzes[int(choice)-1]
                    self._browse_quiz_detail(quiz, category['name'])
                except (IndexError, ValueError):
                    console.print("[red]Invalid selection[/red]")

    
    def _browse_quizzes(self):
        """Browse quizzes with detailed view."""
        if not self.quizzes:
            console.print("[yellow]No quizzes found[/yellow]")
            return
            
        self._display_table(
            "Available Quizzes",
            self.quizzes,
            ["name", "description"],
            show_index=True
        )
        
        while True:
            choice = Prompt.ask(
                "Enter quiz number to view details (0 to go back)",
                choices=[str(i) for i in range(0, len(self.quizzes)+1)]
            )
            
            if choice == "0":
                break
                
            try:
                quiz = self.quizzes[int(choice)-1]
                self._browse_quiz_detail([quiz])
            except (IndexError, ValueError):
                console.print("[red]Invalid selection[/red]")
    
    def _browse_quiz_detail(self, quiz, category_name):
        """Show questions in selected quiz."""
        questions = self._get_questions_by_quiz(quiz['unique_id'])

        console.print(Panel.fit(
            f"[bold]{quiz['name']}[/bold]\n"
            f"[dim]{quiz['description']}[/dim]\n\n"
            f"Category: {category_name}\n"
            f"Questions: {len(questions)}",
            style="blue"
        ))

        if questions:
            self._display_table(
                f"Questions in {quiz['name']}",
                questions,
                ["question_statement", "complex_level"],
                show_index=True
            )

            while True:
                choice = Prompt.ask(
                    "Enter question number to view details (0 to go back)",
                    choices=[str(i) for i in range(0, len(questions)+1)]
                )

                if choice == "0":
                    break

                try:
                    question = questions[int(choice)-1]
                    self._browse_question_detail(question, quiz['name'], category_name)
                except (IndexError, ValueError):
                    console.print("[red]Invalid selection[/red]")

    
    def _browse_questions(self):
        """Browse questions with detailed view."""
        if not self.questions:
            console.print("[yellow]No questions found[/yellow]")
            return
            
        self._display_table(
            "Available Questions",
            self.questions,
            ["question_statement", "complex_level"],
            show_index=True
        )
        
        while True:
            choice = Prompt.ask(
                "Enter question number to view details (0 to go back)",
                choices=[str(i) for i in range(0, len(self.questions)+1)]
            )
            
            if choice == "0":
                break
                
            try:
                question = self.questions[int(choice)-1]
                self._browse_question_detail([question])
            except (IndexError, ValueError):
                console.print("[red]Invalid selection[/red]")
    
    def _browse_question_detail(self, question, quiz_name, category_name):
        """Show detailed view of a question with options and context."""
        response = self._make_request("GET", f"/question/{question['unique_id']}")
        if response:
            data = response.json()
            options = data['options']

            options_text = "\n".join(
                f"{i+1}. {opt['option_statement']}"
                for i, opt in enumerate(options)
            )

            console.print(Panel.fit(
                f"[bold]{data['question_statement']}[/bold]\n"
                f"[dim]Complexity: {data['complex_level']}[/dim]\n\n"
                f"Category: {category_name}\n"
                f"Quiz: {quiz_name}\n\n"
                f"Options:\n{options_text}",
                title="Question Details",
                style="blue"
            ))

    def start_quiz_flow(self):
        """Start a complete quiz experience with proper category selection."""
        if not self.categories:
            console.print("[red]No categories available[/red]")
            return
            
        # Select category
        console.print(Panel.fit("[bold]Select Quiz Category[/bold]", style="green"))
        self._display_table(
            "Available Categories",
            self.categories,
            ["name"],
            show_index=True
        )
        
        while True:
            choice = Prompt.ask(
                "Enter category number (0 to cancel)",
                choices=[str(i) for i in range(0, len(self.categories)+1)]
            )
            
            if choice == "0":
                return
                
            try:
                category = self.categories[int(choice)-1]
                break
            except (IndexError, ValueError):
                console.print("[red]Invalid selection[/red]")
        
        # Select quiz from category
        quizzes = self._get_quizzes_by_category(category['name'])
        if not quizzes:
            console.print(f"[red]No quizzes found in {category['name']}[/red]")
            return
            
        console.print(Panel.fit(
            f"[bold]Quizzes in {category['name']}[/bold]",
            style="green"
        ))
        self._display_table(
            "Available Quizzes",
            quizzes,
            ["name", "description"],
            show_index=True
        )
        
        while True:
            choice = Prompt.ask(
                "Enter quiz number (0 to cancel)",
                choices=[str(i) for i in range(0, len(quizzes)+1)]
            )
            
            if choice == "0":
                return
                
            try:
                quiz = quizzes[int(choice)-1]
                break
            except (IndexError, ValueError):
                console.print("[red]Invalid selection[/red]")
        
        # Get all questions for the selected quiz
        questions = self._get_questions_by_quiz(quiz['unique_id'])
        if not questions:
            console.print("[red]No questions found in this quiz[/red]")
            return
            
        # Quiz settings
        complexity = Prompt.ask(
            "Select complexity level [easy/medium/hard/all]",
            choices=["easy", "medium", "hard", "all"],
            default="all"
        )
        
        if complexity != "all":
            questions = [q for q in questions if q['complex_level'] == complexity]
            if not questions:
                console.print(f"[red]No {complexity} questions found[/red]")
                return
                
        max_questions = len(questions)
        while True:
            count = Prompt.ask(
                f"Number of questions (1-{max_questions})",
                default=str(min(5, max_questions))
            )
            
            try:
                count = int(count)
                if 1 <= count <= max_questions:
                    break
                console.print(f"[red]Please enter a number between 1-{max_questions}[/red]")
            except ValueError:
                console.print(f"[red]Please enter a number between 1-{max_questions}[/red]")
        
        # Start quiz with selected questions
        self._run_quiz_session(quiz, questions[:count])
    
    def _run_quiz_session(self, quiz, questions):
        """Run the quiz session with selected questions."""
        console.print(Panel.fit(
            f"Starting Quiz: {quiz['name']}\n"
            f"Questions: {len(questions)}",
            style="bold green"
        ))
        
        score = 0
        
        for i, question in enumerate(questions, 1):
            # Get full question details
            response = self._make_request("GET", f"/question/{question['unique_id']}")
            if not response:
                continue
                
            question_data = response.json()
            options = question_data['options']
            
            # Display question
            console.print(Panel.fit(
                f"Question {i}/{len(questions)}\n"
                f"Complexity: {question_data['complex_level']}\n\n"
                f"{question_data['question_statement']}",
                title=f"Score: {score}/{i-1}",
                style="blue"
            ))
            
            # Display options
            for idx, opt in enumerate(options, 1):
                console.print(f"{idx}. {opt['option_statement']}")
            
            # Get user answer
            while True:
                try:
                    choice = Prompt.ask(
                        "Your answer",
                        choices=[str(i) for i in range(1, len(options)+1)]
                    )
                    selected_index = int(choice) - 1
                    selected_option = options[selected_index]
                    break
                except (ValueError, IndexError):
                    console.print(f"[red]Please enter a number between 1-{len(options)}[/red]")
            
            # Check answer
            if selected_option['is_correct']:
                console.print("[green]✓ Correct![/green]")
                score += 1
            else:
                correct_index = next(
                    i for i, opt in enumerate(options) 
                    if opt['is_correct']
                )
                console.print(f"[red]✗ Incorrect! The correct answer was {correct_index+1}[/red]")
            
            console.print()  # Add spacing
        
        # Show results
        percentage = (score / len(questions)) * 100
        if percentage >= 70:
            result_style = "bold green"
            message = "Excellent!"
        elif percentage >= 50:
            result_style = "bold yellow"
            message = "Good effort!"
        else:
            result_style = "bold red"
            message = "Keep practicing!"
        
        console.print(Panel.fit(
            f"Quiz Complete!\n\n"
            f"Correct Answers: {score}/{len(questions)}\n"
            f"Percentage: {percentage:.0f}%\n\n"
            f"{message}",
            style=result_style
        ))
    
    def _manage_categories(self):
        """Admin category management menu with full CRUD."""
        while True:
            console.print(Panel.fit("[bold]Category Management[/bold]", style="bold blue"))
            console.print("1. List Categories")
            console.print("2. Create Category")
            console.print("3. Update Category")
            console.print("4. Delete Category")
            console.print("0. Back to Admin Menu")
            
            choice = Prompt.ask("Select action", choices=["0", "1", "2", "3", "4"])
            
            if choice == "0":
                break
            elif choice == "1":
                self._list_categories()
            elif choice == "2":
                self._create_category()
            elif choice == "3":
                self._update_category()
            elif choice == "4":
                self._delete_category()
    
    def _list_categories(self):
        """List all categories."""
        categories = self._get_categories()
        if not categories:
            console.print("[yellow]No categories found[/yellow]")
            return
            
        self._display_table(
            "Categories",
            categories,
            ["name"],
            show_index=True
        )
    
    def _create_category(self):
        """Create a new category."""
        console.print(Panel.fit("[bold]Create New Category[/bold]", style="green"))
        
        name = Prompt.ask("Category name")
        
        response = self._make_request("POST", "/category", data={"name": name})
        if response and response.status_code == 201:
            console.print("[green]Category created successfully![/green]")
            self.categories = self._get_categories()  # Refresh list
        else:
            console.print("[red]Failed to create category[/red]")
    
    def _update_category(self):
        """Update an existing category."""
        categories = self._get_categories()
        if not categories:
            console.print("[yellow]No categories to update[/yellow]")
            return
            
        category = self._prompt_selection(categories, "Select category to update")
        if not category:
            return
            
        new_name = Prompt.ask("Enter new category name", default=category['name'])
        
        response = self._make_request("PUT", f"/category/{category['name']}", data={"name": new_name})
        if response and response.status_code == 200:
            console.print("[green]Category updated successfully![/green]")
            self.categories = self._get_categories()  # Refresh list
        else:
            console.print("[red]Failed to update category[/red]")
    
    def _delete_category(self):
        """Delete a category."""
        categories = self._get_categories()
        if not categories:
            console.print("[yellow]No categories to delete[/yellow]")
            return
            
        category = self._prompt_selection(categories, "Select category to delete")
        if not category:
            return
            
        if Confirm.ask(f"Are you sure you want to delete '{category['name']}'?"):
            response = self._make_request("DELETE", f"/category/{category['name']}")
            if response and response.status_code == 200:
                console.print("[green]Category deleted successfully![/green]")
                self.categories = self._get_categories()  # Refresh list
            else:
                console.print("[red]Failed to delete category[/red]")
    
    def _manage_quizzes(self):
        """Admin quiz management menu with full CRUD."""
        while True:
            console.print(Panel.fit("[bold]Quiz Management[/bold]", style="bold blue"))
            console.print("1. List Quizzes")
            console.print("2. Create Quiz")
            console.print("3. Update Quiz")
            console.print("4. Delete Quiz")
            console.print("0. Back to Admin Menu")
            
            choice = Prompt.ask("Select action", choices=["0", "1", "2", "3", "4"])
            
            if choice == "0":
                break
            elif choice == "1":
                self._list_quizzes()
            elif choice == "2":
                self._create_quiz()
            elif choice == "3":
                self._update_quiz()
            elif choice == "4":
                self._delete_quiz()
    
    def _list_quizzes(self):
        """List all quizzes."""
        quizzes = self._get_quizzes()
        if not quizzes:
            console.print("[yellow]No quizzes found[/yellow]")
            return
            
        self._display_table(
            "Quizzes",
            quizzes,
            ["name", "description", "category"],
            show_index=True
        )
    
    def _create_quiz(self):
        """Create a new quiz."""
        console.print(Panel.fit("[bold]Create New Quiz[/bold]", style="green"))
        
        name = Prompt.ask("Quiz name")
        description = Prompt.ask("Quiz description")
        
        # Select category
        categories = self._get_categories()
        if not categories:
            console.print("[red]No categories available[/red]")
            return
            
        self._display_table(
            "Available Categories",
            categories,
            ["name"],
            show_index=True
        )
        
        while True:
            choice = Prompt.ask(
                "Select category number",
                choices=[str(i) for i in range(1, len(categories)+1)]
            )
            
            try:
                category = categories[int(choice)-1]
                break
            except (IndexError, ValueError):
                console.print("[red]Invalid selection[/red]")
        
        data = {
            "name": name,
            "description": description,
            "category_name": category['name']
        }
        
        response = self._make_request("POST", "/quiz", data=data)
        if response and response.status_code == 201:
            console.print("[green]Quiz created successfully![/green]")
            self.quizzes = self._get_quizzes()  # Refresh list
        else:
            console.print("[red]Failed to create quiz[/red]")
    
    def _update_quiz(self):
        """Update an existing quiz."""
        quizzes = self._get_quizzes()
        if not quizzes:
            console.print("[yellow]No quizzes to update[/yellow]")
            return

        quiz_preview = self._prompt_selection(quizzes, "Select quiz to update")
        if not quiz_preview:
            return

        # 🔧 Fetch full quiz details
        response = self._make_request("GET", f"/quiz/{quiz_preview['unique_id']}")
        if not response or response.status_code != 200:
            console.print("[red]Failed to fetch full quiz details[/red]")
            return
        quiz = response.json()

        new_name = Prompt.ask("Enter new quiz name", default=quiz['name'])
        new_description = Prompt.ask("Enter new description", default=quiz.get('description', ''))

        # 🔍 Show categories to select from
        categories = self._get_categories()
        self._display_table("Available Categories", categories, ["name"], show_index=True)

        while True:
            choice = Prompt.ask(
                "Select new category number (0 to keep current)",
                choices=[str(i) for i in range(0, len(categories)+1)]
            )

            if choice == "0":
                new_category = quiz.get('category') or quiz.get('category_name') or ""
                if not new_category:
                    console.print("[red]Quiz has no associated category. Please select one.[/red]")
                    continue
                break
            try:
                category = categories[int(choice)-1]
                new_category = category['name']
                break
            except (IndexError, ValueError):
                console.print("[red]Invalid selection[/red]")

        data = {
            "name": new_name,
            "description": new_description,
            "category_name": new_category
        }

        response = self._make_request("PUT", f"/quiz/{quiz['unique_id']}", data=data)
        if response and response.status_code == 200:
            console.print("[green]Quiz updated successfully![/green]")
            self.quizzes = self._get_quizzes()  # Refresh list
        else:
            console.print("[red]Failed to update quiz[/red]")

    
    def _delete_quiz(self):
        """Delete a quiz."""
        quizzes = self._get_quizzes()
        if not quizzes:
            console.print("[yellow]No quizzes to delete[/yellow]")
            return
            
        quiz = self._prompt_selection(quizzes, "Select quiz to delete")
        if not quiz:
            return
            
        if Confirm.ask(f"Are you sure you want to delete '{quiz['name']}'?"):
            response = self._make_request("DELETE", f"/quiz/{quiz['unique_id']}")
            if response and response.status_code == 200:
                console.print("[green]Quiz deleted successfully![/green]")
                self.quizzes = self._get_quizzes()  # Refresh list
            else:
                console.print("[red]Failed to delete quiz[/red]")
    
    def _manage_questions(self):
        """Admin question management menu with full CRUD."""
        while True:
            console.print(Panel.fit("[bold]Question Management[/bold]", style="bold blue"))
            console.print("1. List Questions")
            console.print("2. Create Question")
            console.print("3. Update Question")
            console.print("4. Delete Question")
            console.print("0. Back to Admin Menu")
            
            choice = Prompt.ask("Select action", choices=["0", "1", "2", "3", "4"])
            
            if choice == "0":
                break
            elif choice == "1":
                self._list_questions()
            elif choice == "2":
                self._create_question()
            elif choice == "3":
                self._update_question()
            elif choice == "4":
                self._delete_question()
    
    def _list_questions(self):
        """List all questions."""
        questions = self._get_questions()
        if not questions:
            console.print("[yellow]No questions found[/yellow]")
            return
            
        self._display_table(
            "Questions",
            questions,
            ["question_statement", "complex_level", "quiz_id"],
            show_index=True
        )
    
    def _create_question(self):
        """Create a new question."""
        console.print(Panel.fit("[bold]Create New Question[/bold]", style="green"))
        
        statement = Prompt.ask("Question statement")
        
        # Select complexity
        complexity = Prompt.ask(
            "Complexity level [easy/medium/hard]",
            choices=["easy", "medium", "hard"],
            default="medium"
        )
        
        # Select quiz
        quizzes = self._get_quizzes()
        if not quizzes:
            console.print("[red]No quizzes available[/red]")
            return
            
        quiz = self._prompt_selection(quizzes, "Select quiz for this question")
        if not quiz:
            return
        
        # Get options
        options = []
        correct_index = None
        console.print("[bold]Enter question options (minimum 2 required)[/bold]")
        
        for i in range(1, 5):  # Allow up to 4 options
            option_text = Prompt.ask(f"Option {i} (leave blank to stop)")
            if not option_text and i < 3:
                console.print("[red]You must provide at least 2 options[/red]")
                continue
            if not option_text:
                break
                
            options.append({
                "option_statement": option_text,
                "is_correct": False
            })
        
        # Set correct answer
        if len(options) < 2:
            console.print("[red]Question must have at least 2 options[/red]")
            return
            
        self._display_table(
            "Options",
            [{"num": i+1, "text": opt["option_statement"]} for i, opt in enumerate(options)],
            ["num", "text"],
            show_index=False
        )
        
        while True:
            try:
                correct = int(Prompt.ask(
                    "Which option is correct?",
                    choices=[str(i+1) for i in range(len(options))]
                )) - 1
                options[correct]["is_correct"] = True
                break
            except (ValueError, IndexError):
                console.print(f"[red]Please enter a number between 1-{len(options)}[/red]")
        
        # Prepare data
        data = {
            "question_statement": statement,
            "complex_level": complexity,
            "quiz_unique_id": quiz['unique_id'],
            "options": options
        }
        
        response = self._make_request("POST", "/question", data=data)
        if response and response.status_code == 201:
            console.print("[green]Question created successfully![/green]")
            self.questions = self._get_questions()  # Refresh list
        else:
            console.print("[red]Failed to create question[/red]")
    
    def _update_question(self):
        """Update an existing question."""
        questions = self._get_questions()
        if not questions:
            console.print("[yellow]No questions to update[/yellow]")
            return
            
    
        question = self._prompt_selection(questions, "Select question to update", display_field="question_statement")

        if not question:
            return
            
        # Get current question details
        response = self._make_request("GET", f"/question/{question['unique_id']}")
        if not response:
            console.print("[red]Failed to get question details[/red]")
            return
            
        question_data = response.json()
        
        # Update fields
        new_statement = Prompt.ask(
            "Enter new question statement", 
            default=question_data['question_statement']
        )
        
        new_complexity = Prompt.ask(
            "Enter new complexity [easy/medium/hard]",
            choices=["easy", "medium", "hard"],
            default=question_data['complex_level']
        )
        
        # Select new quiz if needed
        quizzes = self._get_quizzes()
        self._display_table(
            "Available Quizzes",
            quizzes,
            ["name", "description"],
            show_index=True
        )
        
        while True:
            choice = Prompt.ask(
                "Select new quiz number (0 to keep current)",
                choices=[str(i) for i in range(0, len(quizzes)+1)]
            )
            
            if choice == "0":
                new_quiz_id = question_data.get('quiz_unique_id')
                break
                
            try:
                quiz = quizzes[int(choice)-1]
                new_quiz_id = quiz['unique_id']
                break
            except (IndexError, ValueError):
                console.print("[red]Invalid selection[/red]")
        
        # Update options
        options = question_data['options']
        console.print("[bold]Current options:[/bold]")
        for i, opt in enumerate(options, 1):
            console.print(f"{i}. {opt['option_statement']} {'✓' if opt['is_correct'] else ''}")
        
        if Confirm.ask("Do you want to update options?"):
            new_options = []
            console.print("[bold]Enter new options (leave blank to keep current)[/bold]")
            
            for i, opt in enumerate(options, 1):
                new_text = Prompt.ask(
                    f"Option {i}", 
                    default=opt['option_statement']
                )
                new_options.append({
                    "option_statement": new_text,
                    "is_correct": opt['is_correct']
                })
            
            # Update correct answer if needed
            self._display_table(
                "Updated Options",
                [{"num": i+1, "text": opt["option_statement"]} for i, opt in enumerate(new_options)],
                ["num", "text"],
                show_index=False
            )
            
            if Confirm.ask("Do you want to change the correct answer?"):
                while True:
                    try:
                        correct = int(Prompt.ask(
                            "Which option is correct?",
                            choices=[str(i+1) for i in range(len(new_options))]
                        )) - 1
                        # Reset all to incorrect first
                        for opt in new_options:
                            opt['is_correct'] = False
                        new_options[correct]['is_correct'] = True
                        break
                    except (ValueError, IndexError):
                        console.print(f"[red]Please enter a number between 1-{len(new_options)}[/red]")
            
            options = new_options
        
        # Prepare update data
        data = {
            "question_statement": new_statement,
            "complex_level": new_complexity,
            "quiz_unique_id": new_quiz_id,
            "options": options
        }
        
        response = self._make_request("PUT", f"/question/{question['unique_id']}", data=data)
        if response and response.status_code == 200:
            console.print("[green]Question updated successfully![/green]")
            self.questions = self._get_questions()  # Refresh list
        else:
            console.print("[red]Failed to update question[/red]")
    
    def _delete_question(self):
        """Delete a question."""
        questions = self._get_questions()
        if not questions:
            console.print("[yellow]No questions to delete[/yellow]")
            return
        
        question = self._prompt_selection(questions, "Select question to delete", display_field="question_statement")

        if not question:
            return
            
        if Confirm.ask(f"Are you sure you want to delete this question?"):
            response = self._make_request("DELETE", f"/question/{question['unique_id']}")
            if response and response.status_code == 200:
                console.print("[green]Question deleted successfully![/green]")
                self.questions = self._get_questions()  # Refresh list
            else:
                console.print("[red]Failed to delete question[/red]")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Quiz API Client")
    parser.add_argument("--url", help="API base URL", default=API_BASE_URL)
    args = parser.parse_args()
    
    client = QuizClient(base_url=args.url)
    client.load_resources()
    client.show_main_menu()

if __name__ == "__main__":
    main()