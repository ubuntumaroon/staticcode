import ast
import re


# Demo code to parse
from typing import Any

code = """\
# sheep = ['Shawn', 'Blanck', 'Truffy'] # abc
# 
# def get_herd():
#     herd = []
#     for a_sheep in sheep:
#         herd.append(a_sheep)
#         for i in range(3):
#            print(i)
#     return Herd(herd=herd)
import os
from typing import abc

class Herd:
    def __init__(self, herd):
        self.herd = herd

    def shave(self, setting='SMOOTH'):
        for sheep in self.herd:
            print(f"Shaving sheep {sheep} on a {setting} setting")
"""


class AstVistor(ast.NodeVisitor):
    # def visit(self, node: ast.AST) -> Any:
    #     # print(node)
    #     self.generic_visit(node)

    def generic_visit(self, node: ast.AST) -> Any:
        print("child for:", node)
        print(ast.unparse(node))
        for field, value in ast.iter_fields(node):
            print(field, value, end=';')
        print('\n-----')
        super().generic_visit(node)

    # def visit_Assign(self, node:ast.AST) -> Any:
    #     # print(ast.unparse(node))
    #     # for field, value in ast.iter_fields(node):
    #     #     print(field, value)
    #     pass
    #
    #
    #
    # def visit_For(self, node: ast.For) -> Any:
    #     print('start:', node.lineno, node.col_offset)
    #     print('end:', node.end_lineno)
    #     # self.generic_visit(node)


def main():
    tree = ast.parse(code)
    visitor = AstVistor()
    visitor.visit(tree)


if __name__ == "__main__":
    main()
