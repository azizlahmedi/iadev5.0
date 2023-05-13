# -*- coding: utf-8 -*-
import os
import shutil
from collections.abc import Iterable
from contextlib import ExitStack

from adl_codegen import adlcodegen
from delia_parser import ast
from neoxam.champagne import consts
#from patterns.pattern1 import Pattern1
#from patterns.pattern2 import Pattern2
#from patterns.pattern3 import Pattern3
#from patterns.pattern4 import Pattern4
#from patterns.pattern5 import Pattern5
#from patterns.pattern7 import Pattern7

schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'portefeuille.adl')


def get_content(path):
    with open(path, 'r', encoding='latin1') as fd:
        return fd.read()


def set_content(path, content):
    with open(path, 'w', encoding='latin1') as fd:
        return fd.write(content)


def walk(tree, patterns):
    if isinstance(tree, (ast.Schema, ast.Procedure)):
        with ExitStack() as stack:
            for pattern in patterns:
                for rule in pattern.rules:
                    stack.enter_context(rule(pattern, tree))
    for node in tree:
        if isinstance(node, Iterable):
            with ExitStack() as stack:
                for pattern in patterns:
                    for rule in pattern.rules:
                        stack.enter_context(rule(pattern, node))
                walk(node, patterns)


class SourceBackend(object):
    def process(self, procedure_path, procedure_name, src_dir, patterns):
        # Get target paths
        procedure_new_path = os.path.join(src_dir, procedure_name.replace('.', '_') + '.adl')
        schema_new_path = os.path.join(src_dir, os.path.basename(schema_path))
        # Load patterns
        pattern_instances = self.load_patterns(patterns)
        # If no pattern, simple copy
        if not pattern_instances:
            shutil.copy(procedure_path, procedure_new_path)
            shutil.copy(schema_path, schema_new_path)
            return procedure_new_path
        # If has pattern, apply them
        schema_content = get_content(schema_path)
        procedure_content = get_content(procedure_path)
        schema_tree = adlcodegen.compile_schema(schema_content)
        walk(schema_tree, pattern_instances)
        schema_new_content, procedure_new_content = adlcodegen.compile(procedure_content, schema_tree, walk,
                                                                       pattern_instances)
        # Store the new contents
        set_content(schema_new_path, schema_new_content)
        set_content(procedure_new_path, procedure_new_content)
        # Return the new procedure path
        return procedure_new_path

    #def load_patterns(self, patterns):
        instances = []
        if consts.FOR_EACH in patterns and consts.SELECT in patterns:
            instances.append(Pattern3())
        else:
            if consts.FOR_EACH in patterns:
                instances.append(Pattern1())
            if consts.FUNCTION in patterns:
                instances.append(Pattern2())
        if consts.FUNCTION in patterns:
            instances.append(Pattern5())
        if consts.REPORT in patterns:
            instances.append(Pattern4())
        if consts.BRANCH in patterns:
            instances.append(Pattern7())
        return instances
