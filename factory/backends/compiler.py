# -*- coding: utf-8 -*-
import json
import logging
import os
import subprocess

#from delia_tokenizer.ctokenize import ScannerFromFile

import delia_commons
from delia_parser import ast, annotate
from delia_parser.compile_context import CompileContext
from delia_parser.parser import gen_ast, parse
from delia_parser.visitor import walk
from delia_preprocessor import scan
from factory import consts
from factory.backends.base import get_project_path, support_environ, compiler_lt

log = logging.getLogger(__name__)


class AnnotatedAstVistor:
    def __init__(self):
        self.__compile_ctx = None

    @property
    def compile_ctx(self):
        return self.__compile_ctx

    @compile_ctx.setter
    def compile_ctx(self, ctx):
        self.__compile_ctx = ctx


class CompilerBackend(object):
    def __init__(self, timeout):
        self.timeout = timeout

    def get_compatibility_version(self, support_home, compiler_version):
        # Retro compatibility
        if compiler_lt(compiler_version, '1.0.5'):
            return compiler_version
        # Get environment
        env = support_environ(support_home)
        # Get compatibility version
        return subprocess.check_output(['deliac', '--compatibility-version'], env=env, timeout=self.timeout, stderr=subprocess.STDOUT).decode('utf-8', 'replace').strip()

    def compile(self, support_home, compiler_version, checkout, schema_version, procedure_name, revision, output_dir):
        if procedure_name == consts.SCHEMA_NAME:
            return self.compile_schema(support_home, checkout, schema_version, output_dir)
        return self.compile_procedure(support_home, compiler_version, checkout, schema_version, procedure_name, revision, output_dir)

    def compile_procedure(self, support_home, compiler_version, checkout, schema_version, procedure_name, revision, output_dir, bytecode=True, mapping=True, json_errors=False, macro_to_function=False):
        # Outputs
        procedure_basename = procedure_name.replace('.', '_')
        output_paths = [
            os.path.join(output_dir, procedure_basename + '.py'),
        ]
        if bytecode:
            output_paths.append(os.path.join(output_dir, procedure_basename + '.pyc'))
        if mapping:
            output_paths.append(os.path.join(output_dir, procedure_basename + '.map.gz'))
        # Meta data
        meta = {'SCHEMA_VERSION': schema_version, }
        if revision is not None:
            meta['REVISION'] = revision
        # Command
        command = [
            'deliac',
            '-p', get_project_path(checkout, schema_version),
            '-o', output_dir,
            '-n', procedure_name,
            '-j', json.dumps(meta),
        ]
        if bytecode:
            command.append('-b')
        if mapping:
            command.append('-m')
        if macro_to_function:
            command.append('-t')
        if json_errors:
            if compiler_lt(compiler_version, '1.0.1'):
                command.append('-J')
            else:
                command.extend(['--error-format', 'json'])
        # Execute
        return self.execute(support_home, command, output_dir, output_paths)

    def gen_annotated_ast(self, checkout, schema_version, procedure_name):

        def gen_tree(scanner, compile_ctx):
            tokens = scan(scanner, scanner.path, files=compile_ctx.files, acros=compile_ctx.macros)
            parser = gen_ast.Parser(verbose=False)
            parse(compile_ctx, tokens=iter(tokens), parser=parser)

        project_path = get_project_path(checkout, schema_version)
        delia_commons.Context().initialize(project_path)
        compile_ctx = CompileContext(root=ast.Root())

        schema_basename = consts.SCHEMA_NAME.replace('.', '_')
        schema_path = delia_commons.DeliaFile(delia_commons.Context(), True, schema_basename).path
        procedure_basename = procedure_name.replace('.', '_')
        procedure_path = delia_commons.DeliaFile(delia_commons.Context(), True, procedure_basename).path

        schema_scanner = ScannerFromFile(schema_path)
        gen_tree(schema_scanner, compile_ctx=compile_ctx)

        procedure_scanner = ScannerFromFile(procedure_path)
        gen_tree(procedure_scanner, compile_ctx=compile_ctx)
        walk(compile_ctx.ast, annotate.Annotator(compile_ctx))
        return compile_ctx

    def compile_schema(self, support_home, checkout, schema_version, output_dir, bytecode=True):
        # Outputs
        schema_basename = consts.SCHEMA_NAME.replace('.', '_')
        output_paths = [
            os.path.join(output_dir, schema_basename + '.py'),
        ]
        if bytecode:
            output_paths.append(os.path.join(output_dir, schema_basename + '.pyc'))
        # Command
        command = [
            'deliac-schema',
            '-p', get_project_path(checkout, schema_version),
            '-s', consts.SCHEMA_NAME,
            '-o', output_dir,
        ]
        if bytecode:
            command.append('-b')
        # Execute
        return self.execute(support_home, command, output_dir, output_paths)

    def execute(self, support_home, command, output_dir, output_paths):
        # Clean
        for output_path in output_paths:
            if os.path.isfile(output_path):
                os.remove(output_path)
        # Create folder
        os.makedirs(output_dir, exist_ok=True)
        # Get environment
        env = support_environ(support_home)
        # Execute
        output = subprocess.check_output(command, env=env, timeout=self.timeout, stderr=subprocess.STDOUT).decode(
            'utf-8', 'replace')
        # Check generated files
        for output_path in output_paths:
            if not os.path.isfile(output_path):
                raise ValueError('failed to generate %s:\n%s' % (output_path.split('.', 1)[-1], output))
        # Return compilation output
        return output
