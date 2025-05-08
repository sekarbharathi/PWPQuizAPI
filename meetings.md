# Meetings notes

## Meeting 1.
* **DATE:** 28.01.2025
* **Course Staff:** Iván Sánchez Milara
* **ASSISTANTS:** An Vu, Bharathi Sekar, Chamudi Vidanagama

### Minutes

* **API Overview**

More details needs to be added in API introduction. Clarify the relationship between questions and quizzes. Explain the role of categories in the system. Distinguish clearly between authentication and authorization, especially when discussing user permissions and types.

* **Main Concepts**

Key concepts like quizzes, questions, categories, and users were mentioned, but definitions are unclear. Answers were not included which they should be added. In diagram, The term "belongs to" needs clarification and include missing components such as answers and difficulty level in the diagram.

* **API Uses**

API is described as being used by two clients, but this should be expanded. No services (e.g., backend systems, integrations) were described. Clarify what clients are using the API and how.

* **Related Work**

Very limited description. No links provided to support claims (e.g., whether Quizlet is RESTful/CRUD-based). Test the Trivia API endpoints and include concrete results. No client application examples were provided, should include some real-world use cases or app examples.

### Action points

* Clarify how questions, quizzes, and categories are related in the API.

* Clearly define authentication and authorization roles.

* Redesign and improve the concept diagram:

* Define all entities clearly.

* Add answers and difficulty.

* Expand the explanation on API clients and identify any services involved.

* Provide concrete links and test results for Trivia API.

* Add examples of existing applications (e.g., client apps using similar APIs).

* Define all core concepts clearly in documentation, including answers.




## Meeting 2.
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




## Meeting 3.
* **DATE: 2025-03-20**
* **ASSISTANTS: Mika Oja**

### Minutes
*Summary of what was discussed during the meeting*

Feedback was provided for the PWP API after the evaluation.

Issues identified in the project structure, code organization, and documentation were discussed.

Specific problems with the PUT method for questions were noted for correction.

Suggestions for improving the resource table in the wiki were analyzed.

Additional extras like URL converters were discussed as opportunities to gain remaining points.

A plan to restructure the project directory and apply code formatting tools was proposed.

The importance of test coverage and validation after modifications was emphasized.

### Action points
*List here the actions points discussed with assistants*

* Fix inaccuracies in the resource table by clearly distinguishing between category and individual category endpoints.

* Move application source code into a separate folder to improve structure.

* Add a .gitignore file to remove unnecessary items like __pycache__, venv, and the database file.

* Refactor views into proper resource classes and clean up formatting in model files.

* Use black to automatically format Python files and ensure line length consistency.

* Correct the PUT method for questions to handle invalid quiz_id properly.

* Implement Flask-style URL converters to improve routing and gain extra points.

* Re-run the test suite to confirm coverage remains high and catch any new issues.

* Optionally improve logging and error handling for robustness and potential bonus marks.




## Meeting 4.
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




## Midterm meeting
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




## Final meeting
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




