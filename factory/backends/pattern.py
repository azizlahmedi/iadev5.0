# -*- coding: utf-8 -*-
import json
import logging
import os
import re
import subprocess
import sys
import tempfile

import delia_parser
from delia_parser.visitor import walk
from factory import consts
from factory.backends.base import TechnicalTest
from factory.backends.compiler import CompilerBackend

log = logging.getLogger(__name__)


class PatternBackend(object):
    def __init__(self, compiler_backend):
        self.compiler_backend = compiler_backend

    def run_technical_tests(self, checkout, schema_version, procedure_name, skip_on_annotate_error, sandbox=False):
        return self.run(checkout, schema_version, procedure_name, visitor_classes=(Y2K,), skip_on_annotate_error=skip_on_annotate_error, sandbox=sandbox)

    def run(self, checkout, schema_version, procedure_name, visitor_classes, skip_on_annotate_error, sandbox=False):
        if sandbox:
            # Can't use multiprocessing with Celery
            with tempfile.TemporaryDirectory() as temp:
                json_path = os.path.join(temp, 'data.json')
                command = [
                    sys.executable,
                    __file__,
                    checkout,
                    str(schema_version),
                    procedure_name,
                    ','.join(v.KEY for v in visitor_classes),
                    str(int(skip_on_annotate_error)),
                    str(self.compiler_backend.timeout),
                    json_path
                ]
                subprocess.check_output(command, timeout=self.compiler_backend.timeout, stderr=subprocess.STDOUT).decode('utf-8', 'replace')
                with open(json_path, 'r', encoding='utf-8') as fd:
                    errors = json.load(fd)
        else:
            errors = self._run(checkout, schema_version, procedure_name, visitor_classes, skip_on_annotate_error)
        technical_tests = []
        for key, logs in errors.items():
            technical_tests.append(TechnicalTest(key, len(logs) == 0, '\n'.join(logs)))
        return technical_tests

    def _run(self, checkout, schema_version, procedure_name, visitor_classes, skip_on_annotate_error):
        errors = {}
        for visitor_class in visitor_classes:
            errors[visitor_class.KEY] = []
        try:
            ctx = self.compiler_backend.gen_annotated_ast(
                checkout,
                schema_version,
                procedure_name,
            )
        except Exception as e:
            if not skip_on_annotate_error:
                for visitor_class in visitor_classes:
                    errors[visitor_class.KEY].append(str(e))
        else:
            for visitor_class in visitor_classes:
                visitor = visitor_class(ctx)
                try:
                    walk(ctx.ast.procedure, visitor)
                except Exception as e:
                    errors[visitor_class].append(str(e))
                errors[visitor_class.KEY].extend(visitor.errors)
        return errors


class BaseVisitor(object):
    def __init__(self, ctx):
        self.ctx = ctx
        self.errors = []


class Y2K(BaseVisitor):
    KEY = consts.TECHNICAL_TEST_KEY_Y2K
    FIELDS_TO_IGNORE = (
        'ccd.date.saisie',
        'bsdb.date.saisie',
        'cchd.date.saisie',
        'cc8cd.date.saisie',
        'bsdpb.date.saisie',
        'ccd.date.8c',
        'bh.ccd.date.saisie',
        'bh1.ccd.date.saisie',
        'bsdbn.date.saisie',
    )
    VALID_DATE_FORMAT_RE = re.compile('.*YYY[Y|B].*', re.IGNORECASE)

    def check_y2k(self, node):
        previous_definition = node.definition
        for conversion_type in node.conversion_types:
            if (isinstance(previous_definition.type, delia_parser.types.String)
                    and isinstance(conversion_type.type, delia_parser.types.Date)
                    and conversion_type.picture.value):

                previous_picture = delia_parser.pictures.StringPicture(str(previous_definition.picture.value))
                previous_picture.validate()
                conversion_type_picture = str(conversion_type.picture.value)
                msg = ''

                if previous_picture.size < len(conversion_type_picture):
                    msg = f'the size of {previous_picture} is smaller than the size of {conversion_type.picture.value}'
                elif self.VALID_DATE_FORMAT_RE.match(conversion_type_picture) is None:

                    msg = f'{conversion_type.picture} is year 2000 bug'

                if msg:
                    messages = [msg]
                    try:
                        from delia_commons.exceptions import gen_macro_exceptions
                    except ImportError:
                        log.warn('upgrade compiler to get full details')
                    else:
                        macro_stack = [(self.ctx.macro_list[idx], m_lineno, m_col, self.ctx.files[m_path]) for idx, m_lineno, m_col, m_path in node.macro_stack]
                        for _, m_message, m_filename, m_lineno, _ in gen_macro_exceptions(1, msg, node.path, node.lineno, node.column, macro_stack):
                            messages.append(f'{m_message}, {m_filename}:{m_lineno}')

                    self.errors.append('\n'.join(messages))

            previous_definition = conversion_type

    def visit_Id(self, node):
        if str(node.name) not in self.FIELDS_TO_IGNORE:
            if len(node.conversion_types) > 0 and node.definition is not None and isinstance(node.definition.type, delia_parser.types.String):
                self.check_y2k(node)


if __name__ == '__main__':
    checkout, schema_version, procedure_name, visitor_class_keys, skip_on_annotate_error, compiler_timeout, json_path = sys.argv[1:]
    schema_version = int(schema_version)
    compiler_timeout = int(compiler_timeout)
    skip_on_annotate_error = bool(int(skip_on_annotate_error))
    visitor_classes = []
    for visitor_class_key in visitor_class_keys.split(','):
        visitor_class = {
            Y2K.KEY: Y2K,
        }[visitor_class_key]
        visitor_classes.append(visitor_class)
    backend = PatternBackend(CompilerBackend(compiler_timeout))
    errors = backend._run(checkout, schema_version, procedure_name, visitor_classes, skip_on_annotate_error)
    with open(json_path, 'w', encoding='utf-8') as fd:
        fd.write(json.dumps(errors))
