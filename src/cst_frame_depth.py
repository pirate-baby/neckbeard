from pathlib import Path
import libcst as cst
from typing import List, Dict, Set, Optional, Tuple
import logging
import sys

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

class FunctionDepthAnalyzer(cst.CSTVisitor):
    """
    Analyze a module to extract:
    - The frame depth of each method or function
    - Functions or methods called within each function/method
    """
    def __init__(self, module_name: str):
        self.module_name = module_name
        self.current_depth = 0
        self.function_depths: Dict[str, int] = {}
        self.call_graph: Dict[str, List[str]] = {}
        self.current_function: Optional[str] = None

    def visit_FunctionDef(self, node: cst.FunctionDef):
        # Increase nesting depth and mark current function
        self.current_depth += 1
        self.current_function = f"{self.module_name}.{node.name.value}"
        logger.info(f"Entering function: {self.current_function} at depth {self.current_depth}")

        # Record the current function's depth
        self.function_depths[self.current_function] = self.current_depth
        self.call_graph[self.current_function] = []  # Initialize call list

    def leave_FunctionDef(self, node: cst.FunctionDef):
        # Reduce nesting depth and leave current function
        logger.info(f"Leaving function: {self.current_function} from depth {self.current_depth}")
        self.current_depth -= 1
        self.current_function = None

    def visit_Call(self, node: cst.Call):
        """
        Track method calls in the current function by recording their names.
        Assume all calls are fully qualified (e.g., module_name.function_name)
        or rely on resolving imported methods.
        """
        if not self.current_function:
            return  # Only process calls within function definitions

        # Handle Attribute calls: module.method()
        if isinstance(node.func, cst.Attribute) and isinstance(node.func.value, cst.Name):
            called_function = f"{node.func.value.value}.{node.func.attr.value}"
            logger.info(f"Function {self.current_function} calls {called_function}")
            self.call_graph[self.current_function].append(called_function)

        # Handle Name calls: method()
        elif isinstance(node.func, cst.Name):
            called_function = node.func.value
            logger.info(f"Function {self.current_function} calls {called_function}")
            self.call_graph[self.current_function].append(called_function)


def analyze_module(file_content: str, module_name: str) -> Tuple[Dict[str, int], Dict[str, List[str]], List[str]]:
    """
    Parse a module and return:
    - function_depths: depths of all functions/methods
    - call_graph: functions/methods called within each function
    - errors: list of syntax errors encountered
    """
    try:
        module_tree = cst.parse_module(file_content)
        analyzer = FunctionDepthAnalyzer(module_name)
        module_tree.visit(analyzer)
        return analyzer.function_depths, analyzer.call_graph, []
    except cst.ParserSyntaxError as e:
        logger.error(f"Syntax error in module {module_name}, skipping: {e}")
        return {}, {}, [f"Syntax error in module {module_name}, skipping: {e}"]

def resolve_total_depths(function_depths: Dict[str, int], call_graph: Dict[str, List[str]]) -> Dict[str, int]:
    """
    Resolve the total depth for all functions/methods by combining call relationships.
    """
    total_depths = {}

    def calculate_depth(func_name: str, visited: Set[str]) -> int:
        if func_name in total_depths:
            return total_depths[func_name]
        if func_name not in function_depths:
            return 0  # Unknown functions have depth 0

        if func_name in visited:
            return function_depths[func_name]  # Avoid recursion for cycles

        visited.add(func_name)
        base_depth = function_depths[func_name]
        cumulative_depth = base_depth

        for called_func in call_graph.get(func_name, []):
            cumulative_depth += calculate_depth(called_func, visited)

        total_depths[func_name] = cumulative_depth
        visited.remove(func_name)
        return cumulative_depth

    for func in function_depths.keys():
        calculate_depth(func, set())
    return total_depths

def analyze_package(package_path: Path) -> dict:
    """Reviews the entire package for maximum depth calls, excluding test files.

    Returns:
        a report of the max depth and related statistics.
    """
    logger.info(f"Analyzing package at path: {package_path}")
    function_graph = {}
    call_graph = {}
    errors = []

    for file_path in package_path.rglob("*.py"):
        # Exclude test files and directories
        if (
            "test" in file_path.parts
            or "tests" in file_path.parts  # Directory or subdirectory contains 'test'
            or file_path.stem.startswith("test_")  # File starts with 'test_'
            or file_path.stem.endswith("_test")    # File ends with '_test'
        ):
            logger.info(f"Skipping test file: {file_path}")
            continue
        if "venv" in file_path.parts:
            logger.info(f"Skipping virtual environment file: {file_path}")
            continue

        logger.info(f"Processing file: {file_path}")
        try:
            source_code = file_path.read_text(encoding="utf-8")
            file_function_depths, file_call_graph, file_errors = analyze_module(source_code, file_path.stem)
            function_graph.update(file_function_depths)
            call_graph.update(file_call_graph)
            errors.extend(file_errors)
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            errors.append(str(e))

    total_depths = resolve_total_depths(function_graph, call_graph)

    # Statistical calculations
    if total_depths:
        max_result = max(total_depths, key=total_depths.get)
        mean_average_depth = sum(total_depths.values()) / len(total_depths)
        standard_deviation_of_depth = (
            sum([(x - mean_average_depth) ** 2 for x in total_depths.values()]) / len(total_depths)
        ) ** 0.5

        # Exclude single-node depths (value of 1)
        excluding_ones = {k: v for k, v in total_depths.items() if v != 1}
        if excluding_ones:
            mean_average_depth_excluding_ones = sum(excluding_ones.values()) / len(excluding_ones)
            standard_deviation_of_depth_excluding_ones = (
                sum([(x - mean_average_depth_excluding_ones) ** 2 for x in excluding_ones.values()])
                / len(excluding_ones)
            ) ** 0.5
        else:
            mean_average_depth_excluding_ones = 0
            standard_deviation_of_depth_excluding_ones = 0

        logger.info(f"Package analysis complete. Max depth: {total_depths[max_result]}, Max depth function: {max_result}")
    else:
        logger.warning("No valid Python functions found.")
        max_result = None
        mean_average_depth = 0
        standard_deviation_of_depth = 0
        mean_average_depth_excluding_ones = 0
        standard_deviation_of_depth_excluding_ones = 0

    return {
        "count_of_functions": len(function_graph),
        "count_of_errors_while_parsing": len(errors),
        "max_depth": total_depths.get(max_result, 0) if max_result else 0,
        "mean_average_depth": round(mean_average_depth,2),
        "max_depth_function": max_result,
        "standard_deviation": round(standard_deviation_of_depth,3),
        "mean_average_depth_excluding_ones": round(mean_average_depth_excluding_ones, 2),
        "standard_deviation_excluding_ones": round(standard_deviation_of_depth_excluding_ones, 3)
    }