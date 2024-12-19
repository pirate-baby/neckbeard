#import json
#from pathlib import Path
#from subprocess import run, PIPE

#def check_dryness() -> dict:
    #"""Check the dryness of the code in Paths by running jscpd in the terminal."""
    #command = ["jscpd", "--max-lines", "5000", "--min-tokens", "30", "--format", "python", "--ignore", "/codebase/venv", "--reporters", "json"]
    #result = run(command, shell=True, cwd="/codebase")
    #if result.returncode != 0:
        #raise Exception(f"jscpd failed with error code {result.returncode}: {result.stdout}\n{result.stderr}")
    #for file in Path("/codebase/report").rglob("*.json"):
        #return json.loads(file.read_text())["statistics"]["total"]

import sys
import hashlib
import logging
from collections import Counter
import libcst as cst
from libcst._exceptions import ParserSyntaxError
from libcst.metadata import MetadataWrapper

logging.basicConfig(level=logging.INFO, handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger(__name__)

class BlockHashingVisitor(cst.CSTVisitor):
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

    return {
        "total_hashes": total_hashes,
        "percentage_duplicates": round((len(duplicate_hashes) / total_hashes) * 100, 2)
    }
