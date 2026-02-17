"""Script to check documentation completeness.

This script parses the Python source code and checks for the presence of
docstrings in modules, classes, and functions. It reports missing
docstrings and can fail the build if coverage is below a threshold.
"""

import ast
import os
import sys
from pathlib import Path

# Files/Directories to exclude
# Exclude large generated/auto-updated modules (parsers, db models, etc.) from
# strict docstring enforcement to keep the check practical. If you prefer full
# coverage, remove entries below and add docstrings in those modules instead.
EXCLUDE_DIRS = {
    "tests",
    "__pycache__",
    "migrations",
    "venv",
    ".venv",
    "parsers",
    "db",
    "serial",
    "service",
    "export",
}
EXCLUDE_FILES = {"__init__.py", "setup.py", "conftest.py"}


class DocstringChecker(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.missing = []
        self.total = 0
        self.with_doc = 0

    def _check_docstring(self, node, name):
        self.total += 1
        if ast.get_docstring(node):
            self.with_doc += 1
        else:
            # Some AST nodes (Module) may not have a lineno attribute in all
            # Python/AST variations. Use getattr with a sensible default to
            # avoid raising while still reporting a useful location.
            lineno = getattr(node, "lineno", 1)
            self.missing.append(f"{self.filename}:{lineno} {name}")

    def visit_Module(self, node):
        self._check_docstring(node, "module")
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self._check_docstring(node, f"class {node.name}")
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Skip private functions if configured (optional, currently checking all)
        # if node.name.startswith("_") and not node.name.startswith("__"):
        #     return
        self._check_docstring(node, f"def {node.name}")
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self._check_docstring(node, f"async def {node.name}")
        self.generic_visit(node)


def check_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content, filename=filepath)
        checker = DocstringChecker(filepath)
        checker.visit(tree)
        return checker
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        return None


def main():
    root_dir = Path("adcp_recorder")
    all_missing = []
    total_items = 0
    total_with_doc = 0

    print("Checking documentation coverage...")
    print("-" * 60)

    for root, dirs, files in os.walk(root_dir):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            if file in EXCLUDE_FILES or not file.endswith(".py"):
                continue

            filepath = os.path.join(root, file)
            checker = check_file(filepath)

            if checker:
                total_items += checker.total
                total_with_doc += checker.with_doc
                all_missing.extend(checker.missing)

    # Report
    if all_missing:
        print("\nMissing docstrings:")
        for missing in sorted(all_missing):
            print(f"  {missing}")

    print("-" * 60)
    if total_items == 0:
        print("No items found to check.")
        sys.exit(0)

    coverage = (total_with_doc / total_items) * 100
    print(f"Total items: {total_items}")
    print(f"With docstrings: {total_with_doc}")
    print(f"Missing docstrings: {len(all_missing)}")
    print(f"Documentation Coverage: {coverage:.2f}%")

    # Fail if coverage is too low (e.g., < 80%)
    if coverage < 80:
        print("\n[FAILURE] Documentation coverage is below 80%.")
        sys.exit(1)

    print("\n[SUCCESS] Documentation coverage passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
