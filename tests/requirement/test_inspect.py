import os
import json
import warnings

from brakeman.requirement import inspect


REQFILE_DIR = os.path.join(os.path.dirname(__file__), 'reqfiles')

def test_inspect():
    ls = inspect.get_requirement_packages(REQFILE_DIR+'/req1.txt')
    for l in ls:
        print(l.name, l.specs)