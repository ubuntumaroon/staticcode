from __future__ import annotations
import os
import sys
from collections import defaultdict

from pyt.analysis.constraint_table import initialize_constraint_table
from pyt.analysis.fixed_point import analyse
from pyt.cfg import make_cfg
from pyt.core.ast_helper import generate_ast
from pyt.core.project_handler import (
    get_directory_modules,
    get_modules
)
from pyt.usage import parse_args
from pyt.vulnerabilities import (
    find_vulnerabilities,
    get_vulnerabilities_not_in_baseline
)
from pyt.vulnerabilities.vulnerability_helper import SanitisedVulnerability
from pyt.web_frameworks import (
    FrameworkAdaptor,
    is_django_view_function,
    is_flask_route_function as is_fastapi_route_function,
    is_function,
    is_function_without_leading_
)

from pyt.usage import default_blackbox_mapping_file, default_trigger_word_file


def discover_files(targets, excluded_files, recursive=False):
    included_files = list()
    excluded_list = excluded_files.split(",")
    for target in targets:
        if os.path.isdir(target):
            for root, _, files in os.walk(target):
                for file in files:
                    if file.endswith('.py') and file not in excluded_list:
                        fullpath = os.path.join(root, file)
                        included_files.append(fullpath)
                if not recursive:
                    break
        else:
            if target not in excluded_list:
                included_files.append(target)
    return included_files


def retrieve_nosec_lines(
    path
):
    file = open(path, 'r')
    lines = file.readlines()
    return set(
        lineno for
        (lineno, line) in enumerate(lines, start=1)
        if '#nosec' in line or '# nosec' in line
    )


def analyze(files):
    nosec_lines = defaultdict(set)
    cfg_list = list()
    for path in sorted(files):

        directory = os.path.dirname(path)
        project_modules = get_modules(directory, prepend_module_root=True)

        local_modules = get_directory_modules(directory)
        tree = generate_ast(path)

        cfg = make_cfg(
            tree,
            project_modules,
            local_modules,
            path,
            allow_local_directory_imports=False
        )
        cfg_list = [cfg]

        framework_route_criteria = is_fastapi_route_function

        # Add all the route functions to the cfg_list
        FrameworkAdaptor(
            cfg_list,
            project_modules,
            local_modules,
            framework_route_criteria
        )

    initialize_constraint_table(cfg_list)

    analyse(cfg_list)

    vulnerabilities = find_vulnerabilities(
        cfg_list,
        default_blackbox_mapping_file,
        default_trigger_word_file,
        False,
        nosec_lines
    )

    return vulnerabilities
