# AST manual: https://greentreesnakes.readthedocs.io/en/latest/manipulating.html
import ast
import os
import subprocess


def load_ast(path: str):
    """
    Read files in path, and get ast
    """
    with open(path, 'r') as f:
        return ast.parse(f.read())