from typing import Generator
from pathlib import Path
import libcst as cst
from typing import Dict, List, Optional, Tuple
import logging
import sys

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

class TestCounter(cst.CSTVisitor):
    """
    Visitor class to find and count test functions/methods in a module.
    """
    def __init__(self):
        self.test_count: int = 0
        self.in_test_class: bool = False  # Tracks if visiting a test class

    def visit_FunctionDef(self, node: cst.FunctionDef):
        """
        Counts test functions or test methods.
        A test function starts with 'test_'.
        """
        # Check for functions or methods with names starting with 'test_'
        if node.name.value.startswith("test_"):
            logger.info(f"Found test function/method: {node.name.value}")
            self.test_count += 1

    def visit_ClassDef(self, node: cst.ClassDef):
        """
        Tracks classes that represent test classes.
        Test classes typically start with 'Test'.
        """
        if node.name.value.startswith("Test"):
            logger.info(f"Entering test class: {node.name.value}")
            self.in_test_class = True

    def leave_ClassDef(self, node: cst.ClassDef):
        """
        Leaves a test class scope.
        """
        if node.name.value.startswith("Test"):
            logger.info(f"Exiting test class: {node.name.value}")
            self.in_test_class = False

def count_tests_in_module(file_content: str) -> int:
    """
    Counts test functions and methods in a given Python module.

    Args:
        file_content (str): The source code of the module.

    Returns:
        int: The number of test functions or methods found.
    """
    try:
        module_tree = cst.parse_module(file_content)
        counter = TestCounter()
        module_tree.visit(counter)
        return counter.test_count
    except cst.ParserSyntaxError as e:
        logger.error(f"Syntax error in module, skipping: {e}")
        return 0


def filtered_codebase(codebase:Path, glob_by:Optional[str]="*") -> Generator:
    """remove venv files from codebase counts"""
    for p in codebase.rglob(glob_by):
        if "venv" not in p.parts:
            yield p


def count_tests_in_package(package_path: Path) -> Dict[str, int]:
    """
    Counts the number of test functions and methods in an entire package.

    Args:
        package_path (Path): The path to the package directory.

    Returns:
        dict: A dictionary summarizing total tests and tests per file.
    """
    logger.info(f"Scanning package at path: {package_path}")
    total_test_count = 0
    tests_per_file: Dict[str, int] = {}

    for file_path in filtered_codebase(package_path, glob_by="*.py"):
        # Identify test files
        if (
            "test" in file_path.parts  # Directory contains 'test'
            or "tests" in file_path.parts  # Directory contains 'tests'
            or file_path.stem.startswith("test_")  # File starts with 'test_'
            or file_path.stem.endswith("_test")    # File ends with '_test'
        ):
            logger.info(f"Processing test file: {file_path}")
            try:
                source_code = file_path.read_text(encoding="utf-8")
                test_count = count_tests_in_module(source_code)
                tests_per_file[str(file_path)] = test_count
                total_test_count += test_count
            except Exception as e:
                logger.error(f"Error reading file {file_path}: {e}")

    logger.info(f"Total number of tests found: {total_test_count}")
    return {
        "total_tests": total_test_count,
        "tests_per_file": tests_per_file
    }