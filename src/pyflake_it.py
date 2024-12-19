from pathlib import Path
import re
from pyflakes.api import checkRecursive


class OverloadReporter:
    """pyflakes is _really_ only made for the CLI. So we patch the reporter to write to lists instead."""

    def __init__(self):
        self._stdout = []
        self._stderr = []

    def unexpectedError(self, filename, msg):
        self._stderr.append(f"{filename}: {msg}\n")

    def syntaxError(self, filename, msg, lineno, offset, text):
        if text is None:
            line = None
        else:
            line = text.splitlines()[-1]

        # lineno might be None if the error was during tokenization
        # lineno might be 0 if the error came from stdin
        lineno = max(lineno or 0, 1)

        if offset is not None:
            # some versions of python emit an offset of -1 for certain encoding errors
            offset = max(offset, 1)
            self._stderr.append('%s:%d:%d: %s\n' %
                               (filename, lineno, offset, msg))
        else:
            self._stderr.append('%s:%d: %s\n' % (filename, lineno, msg))

        if line is not None:
            self._stderr.append(str(line) + '\n')
            if offset is not None:
                self._stderr.append(re.sub(r'\S', ' ', line[:offset - 1]) +
                                   "^\n")

    def flake(self, message):
        self._stdout.append(str(message) + '\n')


def exclude_unwanted_paths(package_path: Path) -> list:
    """Exclude test and venv paths from the package path."""
    filtered_paths = []
    for file_path in package_path.rglob("*.py"):
        if not file_path.is_dir():
            continue
        if file_path.name == "venv":
            continue
        if "test" in file_path.parts:
            continue
        filtered_paths.append(str(file_path))
    return filtered_paths

def flake_package(package_path: Path, detailed:bool = False) -> dict:
    reporter = OverloadReporter()
    paths = [str(p.absolute()) for p in exclude_unwanted_paths(package_path)]
    try:
        checkRecursive(paths, reporter=reporter)
        if detailed:
            return {"issues": reporter._stdout, "errors": reporter._stderr}
        return {"issues": len(reporter._stdout), "errors": len(reporter._stderr)}
    except RecursionError:
        error_msg = "The code is far too complex for pyflakes to analyze, creating infinite recursion."
        return {"issues": error_msg, "errors": error_msg}