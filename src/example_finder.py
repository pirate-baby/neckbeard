from typing import Optional
import sys
from pathlib import Path
from typing import List
import libcst as cst
import logging
import openai
from pydantic import BaseModel, Field


logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)



class HighlightedExample(BaseModel):
    commentary: str = Field(..., description="Your commentary on the code.")
    score: int = Field(...,
                       description="A value from -10 to +10 indicating the impact of this code on the overall quality of the project.")

class ExampleSet(BaseModel):
    collection: List[HighlightedExample] = Field(...,
                                             description="A list of examples to highlight in the codebase.")

class LabeledExample(HighlightedExample):
    module: str = Field(..., description="The module where this example was found.")

class CodeReviewer:

    max_code_size:int = 256000


    def __init__(self):
        self.client = openai.Client()

    def review_with_llm(self, code:str) -> List[dict]:
        logger.debug("Starting review with LLM")
        prompts = [
        {
            "role": "system",
            "content": ("You are scoring the quality and sophistication of user-provided Python code. Choose up to three examples that illustrate the developer's skill (or lack thereof) and the maturity of the codebase.\n"
                        "If there are no remarkable examples, indicate that as well.\n"
                        "Here are some examples of results you might find:\n"
                        " - 'This module imports a SQlAlchemy model and then calls all the built-in functions, it is not clear that this code adds any functionality and probably does not need to exist.' **score**: -5'\n"
                        " - 'The overload of the shift operator makes instances of this class super natural to read and greatly improves the developer experience!' **score**: +6'\n"
                        " - 'The use of `pathlib.Path` is cleaner and more Pythonic than using `os.path`.' **score**: +3'\n"
                        " - 'The variable name `value` is not descriptive and makes the code harder to understand.' **score**: -2'\n"
                        )
        },
        {
            "role": "user",
            "content": f"This is my code:\n\n```python\n{code}\n```"
        }]

        response = self.client.beta.chat.completions.parse(
            model="gpt-4o",
            messages=prompts,
            response_format=ExampleSet
        )
        return response.choices[0].message.parsed.collection

    def is_too_big_to_review(self, code:str):
        """can we review this code all at once?"""
        too_big = len(code) >= self.max_code_size
        logger.debug(f"Code size check: {len(code)} bytes, too big: {too_big}")
        return too_big

    def review_code(self, code, module_name:Optional[str] = None) -> List[LabeledExample]:
        """Review a Python module, class, or function by sending the code to OpenAI."""
        logger.debug(f"Reviewing code for module: {module_name}")
        examples =  self.review_with_llm(code)
        return self.label_examples(examples, module_name)

    def label_examples(self, examples, module_name):
        """Label the examples with the module name."""
        labeled = []
        for example in examples:
            labeled.append(LabeledExample(module=module_name, **example.model_dump()))
        return labeled

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

    def visit_modules(self, module, filename:Optional[str] = None) -> List[dict]:
        """Visit and analyze the entire module (file)."""
        logger.debug("Visiting entire module")
        module_code_str = module.code

        if not self.is_too_big_to_review(module_code_str):
            return self.review_code(module_code_str, filename)
        else:
            results = self.visit_classes(module)
            results.extend(self.visit_functions(module))
            return results

    def summarize_with_llm(self, examples:List[LabeledExample])-> str:
        logger.debug("Summarizing examples with LLM")
        observations = "\n".join([f"- {e.commentary} **score**: {e.score} ({e.module})" for e in examples])
        prompts = [
        {
            "role": "system",
            "content": "The user will supply you with a list of observations about a codebase, as well as an assigned impact score for each observation. Write an opinionated review of the code based on the observations provided. Be very concise, use no more than 150 words.\n"
        },
        {
            "role": "user",
            "content": observations
        }]

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=prompts
        )
        return response.choices[0].message.content

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
                    HighlightedExample(commentary="This function is too large to review by the LLM!", score=-5)
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
            notables = reviewer.visit_modules(module, filepath.name)
            all_notables.extend(notables)
    return {
        "score": round(
            int(((sum([n.score for n in all_notables]) / len(all_notables)) + 10) / 20,
         2) * 100),
        #"summary": reviewer.summarize_with_llm(all_notables), # summary sucks from oai models. Save it for claude
        "details": [n.model_dump() for n in all_notables]
    }
