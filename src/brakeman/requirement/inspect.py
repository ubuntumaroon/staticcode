from typing import Any, Generator

from packaging.version import Version
from packaging.specifiers import SpecifierSet
from packaging.requirements import Requirement
from safety_db import INSECURE, INSECURE_FULL


def is_comment(line: str) -> bool:
    return str(line).strip().startswith('#')


def versions() -> Generator[str]:
    for v in range(100):
        yield "{0.1f}".format(v / 10)


def specs_intersect(spec1: SpecifierSet, spec2: SpecifierSet) -> bool:
    """
    Check if two specSet intersect
    packaging does not provide the functionality, and no way to get boundary
    a simple method to check
    otherwise use the VRange method
    """
    for v in versions():
        if v in spec1 and v in spec2:
            return True

    return False


def spec_intersect_list(spec1: SpecifierSet, specs: list[SpecifierSet]) -> bool:
    """
    Check spec1 intersect with any of specs
    """
    for spec2 in specs:
        if specs_intersect(spec1, spec2):
            return True
    return False


def parse_file(file: str= 'requirement.txt') -> Generator[int, Requirement]:
    with open(file, 'r') as fp:
        for cnt, line in enumerate(fp):
            line = line.strip()
            if not is_comment(line) and len(line) > 0:
                yield cnt, Requirement(line)


def find_vulnerabilities(package: Requirement) -> list[dict]:
    name, spec = package.name, package.specifier
    if name not in INSECURE_FULL:
        return []

    vulnerabilities = INSECURE_FULL[name]
    exist_vuls = list()
    for vul in vulnerabilities:
        specs = [SpecifierSet(s) for s in vul["specs"]]
        if spec_intersect_list(spec, specs):
            exist_vuls.append(vul)

    return exist_vuls
