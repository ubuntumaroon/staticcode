import os
import json
import warnings

from brakeman.requirement import inspect

REQFILE_DIR = os.path.join(os.path.dirname(__file__), 'reqfiles')


def test_inspect():
    res = inspect.ReqInspector(REQFILE_DIR + '/req1.txt')
    assert res.all_vuls_str() is not ""
