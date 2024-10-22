# Firefly AI Assignment

## Folder Structure
1. src/ 
   * Contains all the source code for the application, organized into subdirectories for modularity.
2. src/common/
   * Contains shared utility functions or classes that can be used across different modules, promoting code reusability.
3. src/usecases/ 
   * Contains example scripts and practical implementations demonstrating how to use the features of the application. These scripts serve as a guide for users to understand functionality and integration.
4. src/main.py 
   * Serves as the entry point for the application. It calls the main method to be called.
5. requirements.txt 
   * Lists all the dependencies required to run the application. It allows users to easily install necessary packages.
6. README.md 
   * The main documentation file for the repository, providing an overview, setup instructions, usage examples, and contribution guidelines.
7. gitignore
   * Specifies which files and directories should be ignored by Git when committing changes, preventing unnecessary files from being tracked.


## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/gautampuneet/firefly-ai-assignment.git
cd firefly-ai-assignment
```

### 2. Setup Virtual Env
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. To Execute the Code as a script
```bash
python src/main.py
In the Input put the File Path and Number of Words you want
```