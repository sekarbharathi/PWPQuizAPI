# Meetings notes

## Meeting 1.
* **DATE: 28.01.2025** 
* **ASSISTANTS: Iván Sánchez Milara** 

### Minutes

* **API Overview:** More details needs to be added in API introduction. Clarify the relationship between questions and quizzes. Explain the role of categories in the system. Distinguish clearly between authentication and authorization, especially when discussing user permissions and types.

* **Main Concepts:** Key concepts like quizzes, questions, categories, and users were mentioned, but definitions are unclear. Answers were not included which they should be added. In diagram, The term "belongs to" needs clarification and include missing components such as answers and difficulty level in the diagram.

* **API Uses:** API is described as being used by two clients, but this should be expanded. No services (e.g., backend systems, integrations) were described. Clarify what clients are using the API and how.

* **Related Work:** Very limited description. No links provided to support claims (e.g., whether Quizlet is RESTful/CRUD-based). Test the Trivia API endpoints and include concrete results. No client application examples were provided, should include some real-world use cases or app examples.

### Action points

* Clarify how questions, quizzes, and categories are related in the API.

* Clearly define authentication and authorization roles.

* Redesign and improve the concept diagram.

* Define all entities clearly.

* Add answers and difficulty.

* Expand the explanation on API clients and identify any services involved.

* Provide concrete links and test results for Trivia API.

* Add examples of existing applications (e.g., client apps using similar APIs).

* Define all core concepts clearly in documentation, including answers.



## Meeting 2.
* **DATE: 17.02.2025** 
* **ASSISTANTS: Mika Oja** 

### Minutes

* **Database Design:**
* Add uniquely identifying strings (e.g., UUIDs) to most tables except for the Category table where it's not necessary.

* **Database Models:**
Relationships are not fully implemented. Foreign key constraints are missing at the database level and this should be defined explicitly in the schema (e.g., via ForeignKey declarations).

### Action points

* Add unique string identifiers to relevant tables (except Category).

* Ensure foreign key relationships are explicitly defined in the database schema, not just in the application logic.



## Meeting 3.
* **DATE: 18.03.2025**
* **ASSISTANTS: Mika Oja**

### Minutes

* Feedback was provided for the PWP API after the evaluation.

* Issues identified in the project structure, code organization, and documentation were discussed.

* Specific problems with the PUT method for questions were noted for correction.

* Suggestions for improving the resource table in the wiki were analyzed.

* Additional extras like URL converters were discussed as opportunities to gain remaining points.

* A plan to restructure the project directory and apply code formatting tools was proposed.

* The importance of test coverage and validation after modifications was emphasized.

### Action points

* Fix inaccuracies in the resource table by clearly distinguishing between category and individual category endpoints.

* Move application source code into a separate folder to improve structure.

* Add a .gitignore file to remove unnecessary items like __pycache__, venv, and the database file.

* Refactor views into proper resource classes and clean up formatting in model files.

* Use black to automatically format Python files and ensure line length consistency.

* Correct the PUT method for questions to handle invalid quiz_id properly.

* Implement Flask-style URL converters to improve routing and gain extra points.

* Re-run the test suite to confirm coverage remains high and catch any new issues.

* Optionally improve logging and error handling for robustness and potential bonus marks.


## Meeting 4 and Midterm meeting
* **DATE: 22.04.2025**
* **ASSISTANTS: Mika Oja**

### Minutes

* Feedback on the PWP project documentation was reviewed in detail.

* Structural issues in the API documentation were pointed out, especially missing parameter definitions in components.

* Missing response codes, such as for invalid media types, were noted.

* Hypermedia design aspects were discussed, including missing custom link relations and lack of backward links.

* Hypermedia implementation was found to be incomplete as existing links lacked method and schema information for non-GET actions.

* Testing issues were discussed as tests could not be run properly from the root directory.

* Suggestions for improving hypermedia control, link relations, and overall connectedness were provided.



### Action points

* Move reusable parameters to the components section in the OpenAPI documentation.

* Add missing response codes, including invalid media type errors.

* Add custom link relations to enhance hypermedia design.

* Implement backward relations to improve API connectedness.

* Include method and schema information in hypermedia links, especially for non-GET actions.

* Expand the use of links to more accurately reflect the hypermedia state diagram.

* Ensure all tests can be run from the project’s root directory.

* Validate that hypermedia-related behavior is properly tested.

* Re-evaluate HAL usage and consider alternatives if it limits hypermedia expressiveness.



## Final meeting
* **DATE:**
* **ASSISTANTS:**

### Minutes
*Summary of what was discussed during the meeting*

### Action points
*List here the actions points discussed with assistants*




