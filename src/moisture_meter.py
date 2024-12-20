import sys
import math
import hashlib
import logging
from collections import Counter
import libcst as cst
from libcst._exceptions import ParserSyntaxError
from libcst.metadata import MetadataWrapper

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

class BlockHashingVisitor(cst.CSTVisitor):
    """tried jscpd, and it just pukes blandness. Probably great for checking PRs, not great for
    code quality on the whole. This pattern seems to much more realistically reflect the DRYness of code."""
    def __init__(self, module):
        # Holds hashes for code blocks
        self.skipped_hashes = 0
        self.hashes = []
        self.module = module

    def visit_IndentedBlock(self, node: cst.IndentedBlock) -> bool:
        """Hash an indented block of code."""
        try:
            code = self.module.code_for_node(node)
            # skip blocks with less than 3 lines inside the block
            if code.count("\n") < 3:
                self.skipped_hashes += 1
                return True
            block_hash = hashlib.sha256(code.encode('utf-8')).hexdigest()
            self.hashes.append(block_hash)
        except Exception as e:
            print(f"Error hashing block: {e}")
        return True

def parse_and_hash_file(file_path):
    """Parse a Python file, and return hashes for indented code blocks."""
    with open(file_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    try:
        module = cst.parse_module(source_code)
        wrapper = MetadataWrapper(module)
    except ParserSyntaxError as e:
        logging.error(f"Error parsing file {file_path}: {e}")
        return []
    visitor = BlockHashingVisitor(module)
    wrapper.visit(visitor)

    return visitor.hashes, visitor.skipped_hashes

def check_dryness(project_path):
    """Check the DRYness of code by comparing hashes for code blocks across all Python files in a directory."""
    all_hashes = []
    skipped_hash_count = 0
    for filepath in project_path:
        for file in filepath.rglob("*.py"):
            if "test" not in file.parts and "tests" not in file.parts:
                file_hashes, skipped_hashes = parse_and_hash_file(file)
                all_hashes.extend(file_hashes)
                skipped_hash_count += skipped_hashes

    hash_counter = Counter(all_hashes)

    duplicate_hashes = {k: v for k, v in hash_counter.items() if v > 1}
    total_hashes = len(all_hashes) + skipped_hash_count
    rule_of_threes = {k: v for k, v in hash_counter.items() if v > 2}

    return {
        "total_code_blocks": total_hashes,
        "duplicated_code_blocks": len(duplicate_hashes),
        "percentage_duplicates": round((len(duplicate_hashes) / total_hashes) * 100, 2),
        "rule_of_threes": len(rule_of_threes),
        "percentage_rule_of_threes": round((len(rule_of_threes) / total_hashes) * 100, 2),
        "dryness_score": _dryness_score(total_hashes, len(duplicate_hashes), len(rule_of_threes))
    }

def _dryness_score(total_code_blocks, duplicated_code_blocks, rule_of_threes):
    """
    Calculate a "dryness score" that accounts for the impact of code size and duplication volume.

    Args:
        total_code_blocks (int): Total number of code blocks in the codebase.
        duplicated_code_blocks (int): Number of duplicated code blocks.
        rule_of_threes (int): Number of code blocks duplicated more than twice.

    Returns:
        float: The dryness score (higher is better).
    """
    percentage_duplicates = duplicated_code_blocks / total_code_blocks
    percentage_rule_of_threes = rule_of_threes / total_code_blocks
    scaling_penalty = 1 + math.log10(total_code_blocks) * percentage_duplicates

    return (1 / scaling_penalty) * (1 - percentage_duplicates) * (1 - percentage_rule_of_threes)