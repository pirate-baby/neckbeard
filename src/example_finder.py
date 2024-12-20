import sys
from pathlib import Path
import json
from typing import List
import libcst as cst
import logging
import openai


logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

class CodeReviewer:

    max_code_size:int = 256000


    def __init__(self):
        self.client = openai.Client()

    def review_with_llm(self, code:str) -> List[dict]:
        logger.debug("Starting review with LLM")
        functions = [
            {
                "type": "function",
                "function": {
                "name": "exceptionally_good_code_found",
                "description": "Extract code that is really impressive, creative, or indicative of best practices, and comment on why you think so.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code_snippet": {"type": "string",
                                         "description": "The code snippet you found that is exceptionally good."},
                        "commentary": {"type": "string",
                                       "description": "Your commentary on what makes this code exceptionally good."},
                        "significance": {"type": "integer",
                                        "description": "A score from 1-10 indicating how impressive this example is."}
                    },
                    "required": ["code_snippet", "commentary"]
                }
            }},
            {
                "type": "function",
                "function": {
                "name": "bad_code",
                "description": "Extract code that is poorly written, unmaintainable, or dangerous, and comment on what makes this so.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code_snippet": {"type": "string",
                                         "description": "The code snippet you found that is bad."},
                        "commentary": {"type": "string",
                                       "description": "Your commentary on what is wrong with this code."},
                        "significance": {"type": "integer",
                                        "description": "A score from 1-10 indicating how important this issue is."}
                    },
                    "required": ["code_snippet", "commentary"]
                }
            }},
            {
                "type": "function",
                "function": {
                "name": "no_remarkable_code_found",
                "description": "This function indicates that the code provided is average and does not contain notably good or bad examples.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }}
        ]

        prompts = [
        {
            "role": "system",
            "content": ("You are a software development teaching robot. Review the user-provided code and execute functions to indicate elements that are remarkably good or bad from a design, readability, or efficiency or quality standpoint. Only point out extremes; if the code is average, call the 'no_remarkable_code_found' function.\n"
                        "examples of good code to point out: - creative and efficient solutions\n- amazing variable naming\n- thinking of edge cases\n\n"
                        "examples of bad code to point out: - hardcoded secrets\n- dangerous code\n- terrible variable naming\n- massive nesting or looping\n- catching bare exceptions\n\n"
            )
        },
        {
            "role": "user",
            "content": f"This is my code:\n\n```python\n{code}\n```"
        }]

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=prompts,
            tools=functions,
            tool_choice="auto"

        )
        notables = []
        for function_ in response.choices[0].message.tool_calls:
            if function_.function.name == "no_remarkable_code_found":
                logger.debug("No remarkable code found")
                return [] # short-circuit if no remarkable code found, even if other functions were called

            args = json.loads(function_.function.arguments)
            notables.append({"name": function_.function.name,
                             "code_snippet": args["code_snippet"],
                             "commentary": args["commentary"],
                             "significance": args["significance"]})
        logger.debug(f"Review results: {notables}")
        return notables

    def is_too_big_to_review(self, code:str):
        """can we review this code all at once?"""
        too_big = len(code) >= self.max_code_size
        logger.debug(f"Code size check: {len(code)} bytes, too big: {too_big}")
        return too_big

    def review_code(self, code, module_name):
        """Review a Python module, class, or function by sending the code to OpenAI."""
        logger.debug(f"Reviewing code for module: {module_name}")
        return self.review_with_llm(code)

    def visit_classes(self, module):
        """Visit and analyze all classes in the module."""
        logger.debug("Visiting classes in module")
        visitor = ClassVisitor(self)
        module.visit(visitor)

    def visit_functions(self, module):
        """Visit and analyze all functions in the module."""
        logger.debug("Visiting functions in module")
        visitor = FunctionVisitor(self)
        module.visit(visitor)

    def visit_modules(self, module) -> List[dict]:
        """Visit and analyze the entire module (file)."""
        logger.debug("Visiting entire module")
        module_code_str = module.code

        if not self.is_too_big_to_review(module_code_str):
            return self.review_code(module_code_str, 'Full Module')
        else:
            results = self.visit_classes(module)
            results.extend(self.visit_functions(module))
            return results


class ClassVisitor(cst.CSTVisitor):
    def __init__(self, reviewer: CodeReviewer):
        self.reviewer = reviewer

    def visit_ClassDef(self, node: cst.ClassDef):
        """Visit and review classes in the AST."""
        class_code = node.body
        class_name = node.name.value
        class_code_str = class_code.deepcode()

        logger.debug(f"Visiting class: {class_name}")

        if not self.reviewer.is_too_big_to_review(class_code_str):
            self.reviewer.review_code(class_code_str, class_name)
            return None
        self.visit_functions_for_class(node)

    def visit_functions_for_class(self, node):
        """Visit methods inside the class and review them separately."""
        logger.debug(f"Visiting functions for class: {node.name.value}")
        for item in node.body:
            if isinstance(item, cst.FunctionDef):
                self.reviewer.visit_functions(item)


class FunctionVisitor(cst.CSTVisitor):
    def __init__(self, reviewer: CodeReviewer):
        self.reviewer = reviewer

    def visit_FunctionDef(self, node: cst.FunctionDef):
        """Visit and review functions in the AST."""
        function_code = node.code
        function_name = node.name.value
        function_code_str = function_code.deepcode()

        logger.debug(f"Visiting function: {function_name}")

        # Check size before sending to OpenAI
        if not self.reviewer.is_too_big_to_review(function_code_str):
            self.reviewer.review_code(function_code_str, function_name)
        else:
            logger.error("This function is too large to review in OpenAI!")
            return [
                {"name": "function_too_large", "code_snippet": function_code_str, "commentary": "This function is too large to review in OpenAI."}
            ]


def find_examples(project_dirs:List[Path]) -> list[dict]:
    """find examples in the codebase"""
    logger.info("Starting example search in project directories")
    all_notables = []
    for project_path in [p for p in project_dirs if p.is_dir()]:
        logger.info(f"Analyzing project file: {project_path}")
        for filepath in project_path.glob("*.py"):
            logger.info(f"Analyzing file: {filepath}")
            reviewer = CodeReviewer()
            module = cst.parse_module(filepath.read_text())
            notables = reviewer.visit_modules(module)
            all_notables.extend(notables)
    logger.info(f"Example search complete. Found {len(all_notables)} notable examples.")
    return all_notables





