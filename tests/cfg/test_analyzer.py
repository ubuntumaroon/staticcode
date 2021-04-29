import sys

from brakeman.cfg.analyzer import analyze

def test_analyze():
    """Simple test and output to a file"""
    target = './tests/cfg/vuls/command_injection.py'
    vuls = analyze(target)

    for i, vul in enumerate(vuls):
        print(f"\nVul {i+1}:")
        print(vul)
