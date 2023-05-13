# -*- coding: utf-8 -*-
import csv
import glob
import logging
import multiprocessing
import os
import re
import shutil
import subprocess
import tempfile

from delia_commons import deliafile
from delia_preprocessor.deliaobject import DeliaObject
from delia_tokenizer import token
from delia_tokenizer.tokenize import get_type, get_token, get_path, get_offset

from factory import consts
from factory.backends.base import delia_context, get_project_path
from factory.deliaobject import Procedure

log = logging.getLogger(__name__)


def ignore_comment_ws(scanner):
    for lexeme in scanner:
        if get_type(*lexeme) not in (token.comment, token.WS):
            yield lexeme


def load_frame_map(path):
    frame_map = {}
    if not os.path.exists(path):
        return frame_map
    with open(path, newline='') as fd:
        reader = csv.DictReader(fd, delimiter=';')
        for row in reader:
            if len(row) == 6:
                frame_map[row['frame_name']] = [
                    (int(row['X']), int(row['Y']), int(row['Z'])),
                    (int(row['new_X']), int(row['new_Y'])),
                ]
    return frame_map


FRAME_MAP_BASENAME = 'frame_map.csv'


class BaseFrameBackend(object):
    def export_frame_map(self, schema_version, procedure_name, revision):
        url = self.url + '/gp{schema_version}/adl/src/gra/java/{procedure_basename}/{basename}'.format(
            schema_version=schema_version,
            procedure_basename=procedure_name.replace('.', '_'),
            basename=FRAME_MAP_BASENAME,
        )
        with tempfile.TemporaryDirectory() as temp:
            path = os.path.join(temp, FRAME_MAP_BASENAME)
            if not self.subversion_backend.safe_export(url, path, revision=max(revision, consts.FRAME_MAP_MIN_REVISION)):
                return {}
            return load_frame_map(path)


class FrameAreaBackend(BaseFrameBackend):
    def __init__(self, subversion_backend, url, sandbox_timeout=5 * 60):
        super(FrameAreaBackend, self).__init__()
        self.subversion_backend = subversion_backend
        self.url = url
        self.sandbox_timeout = sandbox_timeout

    def expanse(self, checkout, schema_version, procedure_name):
        ctx = delia_context()
        ctx.initialize(get_project_path(checkout, schema_version))
        procedure = Procedure(procedure_name)
        procedure_path = deliafile.DeliaFile(ctx, True, procedure_name).path
        with tempfile.TemporaryDirectory() as temp:
            procedure_new_path = os.path.join(temp, os.path.basename(procedure_path))
            with open(procedure_new_path, 'w', encoding='latin1') as fd:
                for line in procedure.listing_gen():
                    fd.write(line)
                    fd.write('\n')
            shutil.move(procedure_new_path, procedure_path)

    def tokenize(self, checkout, schema_version, procedure_name):
        frames = {}
        frame_name = None
        ctx = delia_context()
        ctx.initialize(get_project_path(checkout, schema_version))
        procedure = DeliaObject(procedure_name)
        scanner = ignore_comment_ws(procedure.scan_all())
        for lexeme in scanner:
            lexeme_type = get_type(*lexeme)
            if lexeme_type == token.FRAME:
                lexeme = next(scanner)
                if get_type(*lexeme) == token.mag_name:
                    frame_name = get_token(*lexeme).lower()
            elif frame_name and lexeme_type == token.FRAME_AREA:
                from_lexeme = next(scanner)
                if get_type(*from_lexeme) == token.integer:
                    next(scanner)
                    to_lexeme = next(scanner)
                    if get_type(*to_lexeme) == token.integer:
                        if frame_name in frames:
                            raise ValueError(frame_name)
                        frames[frame_name] = (from_lexeme, to_lexeme)
        return procedure.files, frames

    def fix(self, schema_version, procedure_name, revision, checkout, sandbox=False):
        frame_map = self.export_frame_map(schema_version, procedure_name, revision)
        if not frame_map:
            log.info('frame fix ignored as %d:%s@%d has no frame map', schema_version, procedure_name, revision)
            return
        args = (schema_version, procedure_name, checkout, frame_map)
        if sandbox:
            failure = None
            ctx = multiprocessing.get_context('spawn')
            process = ctx.Process(target=self._fix, args=args)
            process.start()
            process.join(self.sandbox_timeout)
            if process.exitcode is None:
                process.terminate()
                failure = 'timeout'
            elif process.exitcode != 0:
                failure = 'exit: %d' % process.exitcode
            if failure:
                raise ValueError('failed to fix frames of %d:%s@%d (%s)' % (schema_version, procedure_name, revision, failure))
        else:
            self._fix(*args)

    def fix_local(self, schema_version, procedure_name, checkout):
        frame_map_path = os.path.join(checkout, 'gp%d' % schema_version, 'adl', 'src', 'gra', 'java', procedure_name.replace('.', '_').lower(), FRAME_MAP_BASENAME)
        frame_map = load_frame_map(frame_map_path)
        if not frame_map:
            log.info('frame fix ignored as %d:%s has no frame map', schema_version, procedure_name)
            return
        self._fix(schema_version, procedure_name, checkout, frame_map)

    def _fix(self, schema_version, procedure_name, checkout, frame_map):
        # Need to work on expanse as some FRAME.AREA are defined in MACROs T_T
        self.expanse(checkout, schema_version, procedure_name)
        files, frames = self.tokenize(checkout, schema_version, procedure_name)
        patch = {}
        for frame_name, [(X, Y, Z), (new_X, new_Y)] in frame_map.items():
            if frame_name in frames:
                from_lexeme, to_lexeme = frames[frame_name]
                if X != new_X:
                    from_path = files[get_path(*from_lexeme)]
                    from_offset = get_offset(*from_lexeme)
                    from_token = get_token(*from_lexeme)
                    if from_path not in patch:
                        patch[from_path] = []
                    patch[from_path].append((from_offset, from_token, str(new_X)))
                if Y != new_Y:
                    to_path = files[get_path(*to_lexeme)]
                    to_offset = get_offset(*to_lexeme)
                    to_token = get_token(*to_lexeme)
                    if to_path not in patch:
                        patch[to_path] = []
                    patch[to_path].append((to_offset, to_token, str(new_Y)))
        if len(patch) == 0:
            log.info('nothing to fix in %d:%s', schema_version, procedure_name)
        for path, data in patch.items():
            log.info('fix frame in %s for %d:%s', os.path.basename(path), schema_version, procedure_name)
            with open(path, 'rb') as fd:  # offset comes as binaries
                content = fd.read()
            data.sort(key=lambda x: x[0], reverse=True)
            for offset, token, new_token in data:
                log.info('replace %s by %s @%d in %s for %d:%s', token, new_token, offset, os.path.basename(path), schema_version, procedure_name)
                content = content[:offset - len(token)] + new_token.encode('latin1') + content[offset:]
            with open(path, 'wb') as fd:
                fd.write(content)


class FrameBackend(BaseFrameBackend):
    WEBINTAKE_CLIENT_JAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'webintake-client.jar')
    POM_XML = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pom.xml')
    LEGACY_NAME_RE = re.compile('^frm_(?P<X>\d+)_(?P<Y>\d+)_(?P<Z>\d+).java$')
    NAME_RE = re.compile('^frm_(?P<X>\d+)_(?P<Y>\d+).java$')
    MLG_TEMPLATE = '''package %(package)s;

import java.util.*;

public class %(name)s_%(lang)s extends ListResourceBundle
{
\tpublic Object[][] getContents() {
\t\treturn contents;
\t}

\tstatic final Object[][] contents =
\t{
%(contents)s
\t};
}
'''

    def __init__(self, subversion_backend, url, java_home, m2_home, compile_timeout=120):
        super(FrameBackend, self).__init__()
        self.subversion_backend = subversion_backend
        self.url = url
        if not java_home or not os.path.isdir(java_home):
            raise ValueError('JAVA_HOME does not exist: %s' % java_home)
        if not m2_home or not os.path.isdir(m2_home):
            raise ValueError('M2_HOME does not exist: %s' % m2_home)
        self.java_home = java_home
        self.m2_home = m2_home
        self.compile_timeout = compile_timeout

    def is_comment(self, line):
        return line.strip().startswith('//')

    def get_url(self, schema_version, procedure_name):
        return self.url + '/gp{schema_version}/adl/src/gra/java/{procedure_basename}'.format(
            schema_version=schema_version,
            procedure_basename=procedure_name.replace('.', '_'),
        )

    def get_legacy_paths(self, frame_dir):
        return self._get_paths(frame_dir, self.LEGACY_NAME_RE)

    def get_paths(self, frame_dir):
        return self._get_paths(frame_dir, self.NAME_RE)

    def _get_paths(self, frame_dir, pattern):
        frame_paths = []
        if os.path.isdir(frame_dir):
            for bn in os.listdir(frame_dir):
                if pattern.match(bn):
                    frame_paths.append(os.path.join(frame_dir, bn))
        return frame_paths

    def get_new_names(self, frame_dir, frame_map, frame_revisions):
        frames = list(frame_revisions.items())
        frames.sort(key=lambda x: x[1])
        new_names = {}
        areas = []
        for frame_name, (area, new_area) in frame_map.items():
            areas.append(area)
        for frame_path, revision in frames:
            m = self.LEGACY_NAME_RE.match(os.path.basename(frame_path))
            X = int(m.group('X'))
            Y = int(m.group('Y'))
            Z = int(m.group('Z'))
            if (X, Y, Z) not in areas:
                new_names['frm_%d_%d' % (X, Y)] = frame_path
        for frame_name, (area, new_area) in frame_map.items():
            frame_path = os.path.join(frame_dir, 'frm_%d_%d_%d.java' % area)
            if os.path.isfile(frame_path):
                new_names['frm_%d_%d' % new_area] = frame_path
        return new_names

    def get_name(self, frame_path):
        return os.path.basename(frame_path)[:-len('.java')]

    def generate(self, frame_path, frame_new_dir, frame_encoding, frame_new_name=None):
        keys = {}
        frame_name = self.get_name(frame_path)
        if not frame_new_name:
            frame_new_name = frame_name
        frame_new_path = os.path.join(frame_new_dir, frame_new_name + '.java')
        if not os.path.exists(frame_new_dir):
            os.makedirs(frame_new_dir)
        with open(frame_path, encoding=frame_encoding) as frame_fd:
            with open(frame_new_path, 'w', encoding='utf-8') as frame_new_fd:
                content = frame_fd.read()
                if frame_name != frame_new_name:
                    content = content.replace(frame_name, frame_new_name)
                for line in content.splitlines(False):
                    if 'SgfTranslator' in line and self.is_comment(line):
                        frame_new_fd.write(line.replace('//', '', 1) + '\n')
                    elif self.is_comment(line):
                        pass
                    elif 'setText' in line or 'setToolTipText' in line or 'setBeanText' in line or 'setTitle' in line:
                        start = line.find('("')
                        stop = line.rfind('")')
                        key = line[0: line.find('.')].strip().upper()
                        msgid = line[start + 2: stop].replace('\\n', '\n').replace('\\"', '"')
                        if msgid.strip() == '':
                            frame_new_fd.write(line + '\n')
                        else:
                            if 'setToolTipText' in line or 'setBeanText' in line:
                                key += '_T'
                            frame_new_fd.write(line[0: start] + '(trans.getString("' + key + '"))' + line[stop + 2:] + '\n')
                            keys[key] = msgid
                    elif 'Placement' in line:
                        pass
                    else:
                        frame_new_fd.write(line + '\n')
        return keys

    def generate_lang(self, frame_dir, frame_name, lang, mo, keys):
        frame_new_path = os.path.join(frame_dir, frame_name + '_' + lang + '.java')
        with open(frame_new_path, 'w', encoding='utf-8') as frame_new_fd:
            contents = []
            for key, msgid in keys.items():
                # TODO: find stripped
                msgstr = None
                if mo:
                    entry = mo.find(msgid)
                    if entry and entry.msgstr:
                        msgstr = entry.msgstr
                if msgstr is None:
                    msgstr = msgid
                # Strip the message. Why?
                msgstr = msgstr.strip().replace('\r', '').replace('"', '\\"').replace('\n', '\\n')
                contents.append('\t\t{"%s", "%s"}' % (key, msgstr))
            context = {
                'package': os.path.basename(frame_dir),
                'name': frame_name,
                'lang': lang,
                'contents': ',\n'.join(contents)
            }
            frame_new_fd.write(self.MLG_TEMPLATE % context)

    def compile(self, schema_version, procedure_name, frame_dir, class_dir):
        if not os.path.exists(class_dir):
            os.makedirs(class_dir)
        env = os.environ.copy()
        env.pop('CLASSPATH', None)
        env['LANG'] = 'en_US.UTF-8'
        env['JAVA_HOME'] = self.java_home
        env['M2_HOME'] = self.m2_home
        env['PATH'] = os.pathsep.join([
            os.path.join(self.java_home, 'bin'),
            os.path.join(self.m2_home, 'bin'),
            env.get('PATH', ''),
        ])
        src_paths = glob.glob(os.path.join(frame_dir, '*.java'))
        with tempfile.TemporaryDirectory() as temp:
            if schema_version <= 2009:
                command = [
                    os.path.join(self.java_home, 'bin', 'javac'),
                    '-cp', self.WEBINTAKE_CLIENT_JAR,
                    '-nowarn',
                    '-d', class_dir,
                ]
                command.extend(src_paths)
            else:
                command = [
                    os.path.join(self.m2_home, 'bin', 'mvn'),
                    '--file', self.POM_XML,
                    '-Dsrc.directory=' + os.path.dirname(frame_dir),
                    '-Doutput.directory=' + class_dir,
                    '-Dtarget.directory=' + temp,
                ]
            try:
                output = subprocess.check_output(command, env=env, stderr=subprocess.STDOUT, timeout=self.compile_timeout).decode('utf-8', 'replace')
            except subprocess.CalledProcessError as e:
                print(e.output.decode('utf-8', 'replace'))

        for src_path in src_paths:
            bin_path = os.path.join(
                class_dir,
                procedure_name.replace('.', '_'),
                os.path.splitext(os.path.basename(src_path))[0] + '.class',
            )
            if not os.path.isfile(bin_path):
                raise ValueError('class %s for %s does not exist' % (os.path.basename(bin_path), procedure_name))
        return output

    def generate_all(self, schema_version, procedure_name, all_mo, frame_dir, frame_names, encoding):
        # Go threw the frames to process
        for frame_name, frame_path in frame_names.items():
            # Log
            log.info('generate frame %s for %d:%s from %s', frame_name, schema_version, procedure_name, frame_path)
            # Generate the new frame
            keys = self.generate(frame_path, frame_dir, encoding, frame_name)
            # Go threw that supported languages
            for lang, mo in all_mo.items():
                # Log
                log.info('generate %s frame %s for %d:%s', lang, frame_name, schema_version, procedure_name)
                # Generate the new internationalized frame
                self.generate_lang(frame_dir, frame_name, lang, mo, keys)

    def generate_and_compile(self, schema_version, procedure_name, revision, all_mo, output_dir):
        # Log
        log.info('generate frames for %d:%s@%d', schema_version, procedure_name, revision)
        # Get work folder
        with tempfile.TemporaryDirectory() as temp:
            # Inputs
            procedure_basename = procedure_name.replace('.', '_')
            frame_dir = os.path.join(temp, 'frame', procedure_basename)
            frame_new_dir = os.path.join(temp, 'frame_new', procedure_basename)
            # Keep in mind if frames were created
            has_frame = False
            # Get frames URL
            url = self.get_url(schema_version, procedure_name)
            # Checkout frames
            if self.subversion_backend.safe_checkout(url, frame_dir, revision=revision):
                # Get the list of legacy frames
                frame_legacy_paths = self.get_legacy_paths(frame_dir)
                # Check if at least one legacy frame
                if frame_legacy_paths:
                    # Get the frame revisions (to be able to sort them)
                    frame_revisions = self.subversion_backend.get_revisions(frame_legacy_paths)
                    # Get frame mapping
                    frame_map = self.export_frame_map(schema_version, procedure_name, revision)
                    # Map old names with new ones
                    frame_new_names = self.get_new_names(frame_dir, frame_map, frame_revisions)
                    # Generate all frames
                    self.generate_all(schema_version, procedure_name, all_mo, frame_new_dir, frame_new_names, 'latin1')
                    # At least one frame
                    has_frame = True
                # Get the list of new frames
                frame_paths = self.get_paths(frame_dir)
                # Check if at least one new frame
                if frame_paths:
                    # Get frame names
                    frame_names = dict([(self.get_name(frame_path), frame_path) for frame_path in frame_paths])
                    # Generate all frames
                    self.generate_all(schema_version, procedure_name, all_mo, frame_new_dir, frame_names, 'utf-8')
                    # At least one frame
                    has_frame = True
                # Check if at least one frame
                if has_frame:
                    # Log
                    log.info('compile %d:%s frames', schema_version, procedure_name)
                    # Compile all the frames
                    self.compile(schema_version, procedure_name, frame_new_dir, output_dir)
            # No frame, log it
            if not has_frame:
                log.info('%d:%s has no frame', schema_version, procedure_name)

    def generate_and_compile_local(self, schema_version, procedure_name, all_mo, checkout, output_dir, compile_legacy=True):
        # Log
        log.info('generate frames for %d:%s', schema_version, procedure_name)
        # Input
        procedure_basename = procedure_name.replace('.', '_').lower()
        # Frame directory
        frame_dir = os.path.join(checkout, 'gp%d' % schema_version, 'adl', 'src', 'gra', 'java', procedure_basename)
        # Keep in mind if frames were created
        has_frame = False
        # Checkout frames
        if os.path.isdir(frame_dir):
            # Get work folder
            with tempfile.TemporaryDirectory() as temp:
                # Get the new frame directory
                frame_new_dir = os.path.join(temp, procedure_basename)
                # Get the list of legacy frames
                frame_legacy_paths = self.get_legacy_paths(frame_dir)
                # Check if at least one legacy frame
                if frame_legacy_paths:
                    # We have not the revisions
                    frame_revisions = dict([(path, 0) for path in frame_legacy_paths])
                    # Load frame map
                    frame_map = load_frame_map(os.path.join(frame_dir, FRAME_MAP_BASENAME))
                    # Map old names with new ones
                    frame_new_names = self.get_new_names(frame_dir, frame_map, frame_revisions)
                    # Also compile the legacy ones if required
                    if compile_legacy:
                        frame_new_names.update(dict([(self.get_name(frame_legacy_path), frame_legacy_path) for frame_legacy_path in frame_legacy_paths]))
                    # Generate all frames
                    self.generate_all(schema_version, procedure_name, all_mo, frame_new_dir, frame_new_names, 'latin1')
                    # At least one frame
                    has_frame = True
                # Get the list of new frames
                frame_paths = self.get_paths(frame_dir)
                # Check if at least one new frame
                if frame_paths:
                    # Get frame names
                    frame_names = dict([(self.get_name(frame_path), frame_path) for frame_path in frame_paths])
                    # Generate all frames
                    self.generate_all(schema_version, procedure_name, all_mo, frame_new_dir, frame_names, 'utf-8')
                    # At least one frame
                    has_frame = True
                # Check if at least one frame
                if has_frame:
                    # Log
                    log.info('compile %d:%s frames', schema_version, procedure_name)
                    # Compile all the frames
                    self.compile(schema_version, procedure_name, frame_new_dir, output_dir)
        # No frame, log it
        if not has_frame:
            log.info('%d:%s has no frame', schema_version, procedure_name)
