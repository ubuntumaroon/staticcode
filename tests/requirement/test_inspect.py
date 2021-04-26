import os
import json
import warnings

from brakeman.requirement import inspect


REQFILE_DIR = os.path.join(os.path.dirname(__file__), 'reqfiles')


def test_inspect():
    res = list(inspect.parse_file(REQFILE_DIR+'/req1.txt'))
    print(res)