# Neckbeard.py

Neckbeard.py is a Python library that analyzes git repositories to determine the production-quality, utility, and maintainable nature of the code. It assigns an overall rating/score based on these factors.

## Features

- Analyzes git repositories
- Evaluates production-quality of the code
- Assesses utility and maintainability
- Provides an overall rating/score

## Installation

To install Neckbeard.py, use pip:

```bash
pip install neckbeard
```

## Usage

```python
import neckbeard

# Analyze a git repository
repo_path = '/path/to/your/repo'
analysis = neckbeard.analyze(repo_path)

# Get the overall rating/score
score = analysis.get_score()
print(f'Overall Score: {score}')
```

## License

This project is licensed under the MIT License.


## What Is Measured

### Pasta Rating
- average file complexity (Mccabe)
- Maintainability Index of whole project
- nummber of lines of code
- number of files
- max nesting depth
- average nesting depth
- average length per file
- size of the code base
- :white_checkbox: size of the total package including all dependencies

### Dependency Management
- dependency pinning/locking
- total number of required dependencies
- total number of dependencies in the entire dependency chain

### Production-ready
- code coverage and code quality
- standard SCA stuff (linting etc)
- number of deps (who is importing this code?)

