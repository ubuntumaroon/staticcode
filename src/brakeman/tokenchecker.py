# https://deepsource.io/blog/introduction-static-code-analysis/
# https://medium.com/@prasincs/open-source-static-analysis-for-security-in-2018-part-1-python-348e9c1af1cd
# db
# https://github.com/pyupio/safety-db

import ast
import sys
import tokenize


def read_file(filename):
    with tokenize.open(filename) as fd:
        return fd.read()


class BaseChecker(ast.NodeVisitor):
    def __init__(self):
        self.violations = []

    def check(self, path):
        for filepath in path:
            self.filename = filepath
            tree = ast.parse(read_file(filepath))
            self.visit(tree)

    def report(self):
        for violation in self.violations:
            filename, lineno, msg = violation
            print(f"{filename}:{lineno}: {msg}")


class TokenChecker:
    msg = "token checker base class"

    def __init__(self):
        self.violations = []

    def find_violations(self, filename, tokens):
        for token_type, token, (line, col), _, _ in tokens:
            if token_type == tokenize.STRING \
                    and token.startswith("'''") or token.startswith("'"):
                self.violations.append((filename, line, col))

    def check(self, files):
        for filename in files:
            with tokenize.open(filename) as fd:
                tokens = tokenize.generate_tokens(fd.readline)
                self.find_violations(filename, tokens)

    def report(self):
        for violation in self.violations:
            filename, line, col = violation
            print(f"{filename}:{line}:{col}: {self.msg}")


if __name__ == '__main__':
    files = sys.argv[1:]
    checker = TokenChecker()
    checker.check(files)
    checker.report()
