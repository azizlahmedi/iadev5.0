# -*- coding: utf-8 -*-
import contextlib
import ftplib
import os

from delia_commons.deliafile import path_name_convert
from delia_preprocessor.deliaobject import DeliaObject
from delia_preprocessor.iterator import fill
from delia_preprocessor.provider import IProvider
#from delia_tokenizer.ctokenize import ScannerFromFile

from factory import consts
from factory.backends.base import delia_context
from factory.mphash import mphash

try:
    import ssl
except ImportError:
    _SSLSocket = None
else:
    _SSLSocket = ssl.SSLSocket


class Error(Exception):
    pass


class VMSFTP(ftplib.FTP):
    def retrlines(self, cmd, callback=None):
        """Retrieve data in line mode.  A new port is created for you.

        Args:
          cmd: A RETR, LIST, or NLST command.
          callback: An optional single parameter callable that is called
                    for each line with the trailing CRLF stripped.
                    [default: print_line()]

        Returns:
          The response code.
        """
        if callback is None:
            callback = print
        resp = self.sendcmd('TYPE A')
        with self.transfercmd(cmd) as conn, \
                conn.makefile('rb', encoding=self.encoding) as fp:
            while 1:
                line = fp.readline(self.maxline + 1)
                line = line.decode(encoding=self.encoding)
                if len(line) > self.maxline:
                    raise Error("got more than %d bytes" % self.maxline)
                if self.debugging > 2:
                    print('*retr*', repr(line))
                if not line:
                    break
                if line[-2:] == ftplib.CRLF:
                    line = line[:-2]
                elif line[-1:] == '\n':
                    line = line[:-1]
                callback(line)
            # shutdown ssl layer
            if _SSLSocket is not None and isinstance(conn, _SSLSocket):
                conn.unwrap()
        return self.voidresp()


class FTPBackend(object):
    client_class = None

    def __init__(self, host, user, passwd):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.cx = None

    @contextlib.contextmanager
    def connection(self):
        with self.client_class(self.host, self.user, self.passwd) as self.cx:
            yield self
        self.cx = None

    def get_content(self, remote_path, local_path):
        assert self.cx is not None
        cmd = 'RETR {}'.format(remote_path)
        lines = []
        self.cx.retrlines(cmd, lines.append)
        os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
        content = '\n'.join(lines)
        if content and content[-1] != '\n':
            content += '\n'
        with open(local_path, 'w', encoding='latin1') as fd:
            fd.write(content)
        return content


class FTPVmsBackend(FTPBackend):
    client_class = VMSFTP


class FTPUnixBackend(FTPBackend):
    client_class = ftplib.FTP

    def get_dir_content(self, remote_dir, local_dir):
        try:
            remote_paths = self.cx.nlst(remote_dir)
        except ftplib.error_perm as e:
            es = str(e).lower()
            if '550' in es and ('file not found' in es or 'no such file or directory' in es):  # VMS vs. Unix
                return
            raise
        for remote_path in remote_paths:
            self.get_content(remote_path, os.path.join(local_dir, os.path.basename(remote_path)))


class VmsProvider(IProvider):
    def __init__(self, ftp_vms_backend):
        self.ftp_vms_backend = ftp_vms_backend

    def get(self, ctx, is_text, text, father=None):
        local_path = path_name_convert(ctx, text, is_text, father=father)
        if not os.path.exists(local_path):
            rel_path = local_path.replace(ctx.project_path, '', 1).split(os.path.sep, 3)[-1]
            first_dir = rel_path.split(os.path.sep)[0]
            if first_dir == 'mag':
                procedure_name = os.path.splitext(os.path.basename(local_path))[0].replace('_', '.').lower()
                if procedure_name in ctx.mv.get(ctx.schema_version, {}):
                    procedure_hash = ctx.mv[ctx.schema_version][procedure_name]['hash']
                else:
                    procedure_hash = mphash(ctx.schema_name, procedure_name)
                remote_path = 'mag/%s.me0' % procedure_hash
            elif first_dir == 'bib':
                remote_path = 'bib/' + os.path.basename(local_path)
            elif first_dir == 'lib':
                remote_path = 'DISK$300P:[SYS0.SYSCOMMON.MAGNUM.LIBRARY]' + os.path.basename(local_path)
            else:
                remote_path = rel_path.replace(os.path.sep, '/')
            self.ftp_vms_backend.get_content(remote_path, local_path)
        return fill(ScannerFromFile(local_path, skip_ws=True)), local_path


class LegacyBackend(object):
    def __init__(self, vms_host, vms_user, vms_passwd, unix_host, unix_user, unix_passwd):
        self.ftp_vms_backend = FTPVmsBackend(vms_host, vms_user, vms_passwd)
        self.ftp_unix_backend = FTPUnixBackend(unix_host, unix_user, unix_passwd)

    def get_sources(self, project_path, procedure_name):
        ctx = delia_context()
        ctx.initialize(project_path)
        with self.ftp_vms_backend.connection():
            provider = VmsProvider(self.ftp_vms_backend)
            object_names = [consts.SCHEMA_NAME, ]
            if procedure_name != consts.SCHEMA_NAME:
                object_names.append(procedure_name)
            for object_name in object_names:
                delia_object = DeliaObject(object_name, provider=provider)
                for _ in delia_object.get_scanner_include():
                    pass
        procedure_basename = procedure_name.replace('.', '_')
        with self.ftp_unix_backend.connection():
            self.ftp_unix_backend.get_dir_content(
                'gra/java/monolang/java/' + procedure_basename,
                os.path.join(project_path, 'adl', 'src', 'gra', 'java', procedure_basename),
            )
