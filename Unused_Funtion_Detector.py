#!/usr/bin/env python
"""
unused_function_detector.py

This script scans a given Python project folder (recursively) and identifies user‐defined functions 
(either at module level or as class methods) that do not appear to be used anywhere in the project.
It accepts two inputs:
  1. The project folder path.
  2. The virtual environment folder name (to skip scanning files within that folder, if any).

Usage:
    (penv) C:\path\to\project> py unused_function_detector.py
    Enter project folder path: C:\path\to\your\project
    Enter virtual environment name (or press Enter if none): venv

Notes:
  - This is a static analysis tool using Python's ast module. It will not catch dynamic usage.
  - If a function’s name is used as a variable or passed as an argument (e.g. as a callback), it will count as "used".
  - The analysis is based on name matching only. If you have functions with the same name in different modules or classes,
    a single usage might be attributed to all of them.
  - Dunder functions (like __init__, __str__, etc.) and command methods (e.g. Command.handle, Command.add_arguments)
    are excluded from the unused list.
"""

import os
import sys
import ast


class FunctionDefCollector(ast.NodeVisitor):
    """
    Collects all function definitions (both top‐level and class methods) in an AST.
    Stores each function as a tuple: (qualified_name, filename, lineno)
    """
    def __init__(self, filename):
        self.filename = filename
        self.definitions = []  # list of tuples: (qualified_name, filename, lineno)
        self._class_stack = []

    def visit_ClassDef(self, node):
        # Push the class name on the stack and process its body.
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_FunctionDef(self, node):
        # Determine qualified name: include class names if inside a class.
        if self._class_stack:
            qualified_name = ".".join(self._class_stack + [node.name])
        else:
            qualified_name = node.name

        self.definitions.append((qualified_name, self.filename, node.lineno))
        # Process nested functions if any:
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)


class NameUsageCollector(ast.NodeVisitor):
    """
    Collects all names (and attribute names) used in an AST.
    It collects any usage of a name in a Load context.
    """
    def __init__(self):
        self.used_names = set()

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # For an attribute access like obj.func, add the attribute name.
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.attr)
        self.generic_visit(node)


def get_python_files(project_path, venv_name=None):
    """
    Recursively yield full paths to Python (.py) files in the project folder,
    skipping any folders that match the virtual environment name.
    """
    for root, dirs, files in os.walk(project_path):
        # If venv_name is provided, skip that directory
        if venv_name:
            dirs[:] = [d for d in dirs if d.lower() != venv_name.lower()]
        for file in files:
            if file.endswith('.py'):
                yield os.path.join(root, file)


def analyze_project(project_path, venv_name=None):
    """
    Analyze the project folder to collect function definitions and name usages.
    Returns:
      - definitions: list of tuples (qualified_function_name, filename, lineno)
      - used_names: set of all names (strings) that were used somewhere in the code.
    """
    definitions = []
    used_names = set()

    python_files = list(get_python_files(project_path, venv_name))
    if not python_files:
        print("No Python files found in the given project folder.")
        return definitions, used_names

    for file_path in python_files:
        try:
            with open(file_path, encoding='utf-8') as f:
                source = f.read()
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            continue

        try:
            tree = ast.parse(source, filename=file_path)
        except Exception as e:
            print(f"Error parsing file {file_path}: {e}")
            continue

        # Collect function definitions from this file.
        def_collector = FunctionDefCollector(file_path)
        def_collector.visit(tree)
        definitions.extend(def_collector.definitions)

        # Collect name usages from this file.
        usage_collector = NameUsageCollector()
        usage_collector.visit(tree)
        used_names.update(usage_collector.used_names)

    return definitions, used_names


def is_excluded(qualified_name):
    """
    Return True if the function should be excluded from unused analysis.
    Exclusions:
      - Dunder functions (names that start and end with '__')
      - Command methods: For classes named 'Command', exclude 'handle' and 'add_arguments'
    """
    # Get the simple function name (last part of the qualified name)
    simple_name = qualified_name.split(".")[-1]
    if simple_name.startswith("__") and simple_name.endswith("__"):
        return True

    # Exclude methods on a Command class.
    parts = qualified_name.split(".")
    if len(parts) >= 2 and parts[0] == "Command" and simple_name in {"handle", "add_arguments"}:
        return True

    return False


def main():
    print("Unused Function Detector\n")
    project_path = input("Enter project folder path: ").strip()
    if not project_path or not os.path.isdir(project_path):
        print("Invalid project folder path.")
        sys.exit(1)

    venv_name = input("Enter virtual environment name (or press Enter if none): ").strip()
    if venv_name == "":
        venv_name = None

    print("\nAnalyzing project... Please wait.\n")
    definitions, used_names = analyze_project(project_path, venv_name)

    if not definitions:
        print("No function definitions found in the project.")
        sys.exit(0)

    # Identify unused functions: if the function's (simple) name is never used, consider it unused.
    # For qualified names (e.g. ClassName.func), we check the last part.
    unused_functions = []
    for qualified_name, filename, lineno in definitions:
        # Skip if this function should be excluded (e.g., dunder or Command methods)
        if is_excluded(qualified_name):
            continue

        simple_name = qualified_name.split(".")[-1]
        if simple_name not in used_names:
            unused_functions.append((qualified_name, filename, lineno))

    if unused_functions:
        print("The following user‐defined functions appear to be unused:\n")
        for qualified_name, filename, lineno in sorted(unused_functions, key=lambda x: (x[1], x[2])):
            print(f"{qualified_name} -> {filename} (line {lineno})")
    else:
        print("No unused functions detected.")


if __name__ == '__main__':
    main()
