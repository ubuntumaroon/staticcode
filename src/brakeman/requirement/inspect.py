#from safety_db import INSECURE, INSECURE_FULL
from typing import Any

from packaging.version import Version, parse
import requirements
import operator
from .vrange import VRange


def get_requirement_packages(filename: str = 'requirements.txt') -> list:
    with open(filename, 'r') as fd:
        return list(requirements.parse(fd))


class Requirement(object):
    def __init__(self, req: Any) -> None:
        """
        Convert from Requirement object in "requirements" package
        """
        self.line = req.line
        self.name = req.name
        self.path = req.path
        self.raw = req
