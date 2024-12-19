from pathlib import Path
from radon.complexity import cc_visit, ComplexityVisitor
from typing import Dict, List, Tuple
import logging
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

def is_test_file(file_path: Path) -> bool:
    """
    Determine if a file is a test file based on its name or path.
    """
    return (
        "test" in file_path.parts  # Directory contains 'test'
        or file_path.stem.startswith("test_")  # File starts with 'test_'
        or file_path.stem.endswith("_test")    # File ends with '_test'
    )

def is_venv_file(file_path: Path) -> bool:
    """
    Determine if a file is a virtual environment file based on its path.
    """
    return "venv" in file_path.parts


def analyze_file_complexity(file_path: Path) -> List[Tuple[str, int]]:
    """
    Analyzes a single Python file and calculates the cyclomatic complexity
    of its functions and methods.

    Args:
        file_path (Path): Path to the Python file.

    Returns:
        List[Tuple[str, int]]: A list of (function_name, complexity) pairs.
    """
    try:
        source_code = file_path.read_text(encoding="utf-8")
        visitor = ComplexityVisitor.from_code(source_code)
        results = []

        for function in visitor.functions:
            results.append((function.name, function.complexity))
        return results

    except Exception as e:
        logger.error(f"Error analyzing file {file_path}: {e}")
        return []


def analyze_package_complexity(package_path: Path) -> Dict[str, List[Tuple[str, int]]]:
    """
    Analyzes all Python files in a package (excluding test files) for cyclomatic complexity.

    Args:
        package_path (Path): Path to the package directory.

    Returns:
        Dict[str, List[Tuple[str, int]]]: A dictionary mapping file paths to a list
        of (function_name, complexity) pairs.
    """
    complexity_summary: Dict[str, List[Tuple[str, int]]] = {}

    logger.info(f"Analyzing package for cyclomatic complexity: {package_path}")
    for file_path in package_path.rglob("*.py"):
        if is_test_file(file_path) or is_venv_file(file_path):
            logger.info(f"Skipping excluded file: {file_path}")
            continue

        logger.info(f"Analyzing file: {file_path}")
        file_complexities = analyze_file_complexity(file_path)
        complexity_summary[str(file_path)] = file_complexities

    return complexity_summary




def summarize_complexity_results(results: Dict[str, List[Tuple[str, int]]]):
    """
    Summarizes the complexity results: total number of functions analyzed and
    overall statistics for cyclomatic complexity.

    Args:
        results (Dict[str, List[Tuple[str, int]]]): Complexity results for all files.
    """
    total_functions = 0
    complexity_values = []
    max_complexity = {"function": None, "complexity": 0}
    highly_complex_functions = []

    for file, functions in results.items():
        print(f"\nFile: {file}")
        if not functions:
            continue

        for func_name, complexity in functions:
            total_functions += 1
            complexity_values.append(complexity)
            if complexity > max_complexity["complexity"]:
                max_complexity["function"] = func_name
                max_complexity["complexity"] = complexity
            if complexity > 31: # considered high complexity
                highly_complex_functions.append((func_name, complexity))

    if complexity_values:
        avg_complexity = sum(complexity_values) / len(complexity_values)
        max_complexity_val = max_complexity["complexity"]
        max_complexity_func = max_complexity["function"]
        percent_high_complexity = len(highly_complex_functions) / total_functions * 100

        return {
            "mean_average_complexity": round(avg_complexity, 2),
            "max_complexity_function": max_complexity_func,
            "max_complexity": max_complexity_val,
            "percent_high_complexity": round(percent_high_complexity, 2),
        }


def get_package_complexity(package_path: Path) -> dict:
    """
    Entry point to analyze cyclomatic complexity for a Python package.

    Args:
        package_path (str): Path to the package directory.
    """
    if not package_path.is_dir():
        logger.error(f"Invalid directory: {package_path}")
        sys.exit(1)

    results = analyze_package_complexity(package_path)
    return summarize_complexity_results(results)