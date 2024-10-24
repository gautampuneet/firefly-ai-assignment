# Firefly AI Assignment

## Table of Contents

- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Testing](#testing)
- [Technologies Used](#technologies-used)

## Project Structure

The project is structured as follows:

1. src/ 
   * Contains all the source code for the application, organized into subdirectories for modularity.
2. src/common/
   * Contains shared utility functions or classes that can be used across different modules, promoting code reusability.
3. usecases
   * Contains Business level logic for the application.
4. src/main.py 
   * Serves as the entry point for the application. It calls the main method to be called.
5. requirements.txt 
   * Lists all the dependencies required to run the application. It allows users to easily install necessary packages.
6. README.md 
   * The main documentation file for the repository, providing an overview, setup instructions, usage examples, and contribution guidelines.
7. gitignore
   * Specifies which files and directories should be ignored by Git when committing changes, preventing unnecessary files from being tracked.
8. src/server.py
   * Serves as the entry point for the FastAPI web application.
9. routes
   * Includes all the routes that we will be using in this application

## Installation

### Prerequisites

- Python 3.10 or higher
- Virtualenv (optional but recommended)

### Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/gautampuneet/firefly-ai-assignment.git
   cd firefly-ai-assignment
   ```

2. **Setup a Virtual Env(Optional)**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Requirements**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **To Execute the Code as a script**:
   ```bash
   python src/main.py
   ```

2. **To Execute the code as a server**:
   ```bash
   python src/server.py
   ```
   - Default Server Port:- 8000
   - Swagger Docs:- http://localhost:8000/docs

3. **Configuration**:
   Ensure that any necessary constants or configurations are correctly defined in src/common/constants.py before running the application.

## Testing

### Unit tests for this project can be found in the tests/ directory. To run the tests, use:
   ```bash
   python -m unittest tests/usecases/test_essays.py
   
   ```

## Technologies Used

   * Python: Core Programming Language
   * FastAPI(optional): For server handling.
   * Unittest: For testing purposes
   * Git: Version Control
