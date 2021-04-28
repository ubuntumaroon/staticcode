import os
from brakeman.cfg.builder import CFGBuilder


SRC_DIR = os.path.join(os.path.dirname(__file__), '../../src')


# def test_cfg():
#     cfg = CFGBuilder().build_from_file('token', SRC_DIR+'/brakeman/tokenchecker.py')
#     cfg.build_visual('output.pdf', 'pdf')