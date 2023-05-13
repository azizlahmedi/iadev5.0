import ftplib
import tempfile
from neoxam.gpatcher import settings, models
import os
import datetime

try:
    import ssl
except ImportError:
    _SSLSocket = None
else:
    _SSLSocket = ssl.SSLSocket

class Error(Exception): pass

def print_line(line):
    '''Default retrlines callback to print a line.'''
    print(line)

class VMSFTP(ftplib.FTP):

    def retrlines(self, cmd, callback = None):
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
            callback = print_line
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

def get_content(ftp, username, password, src, path):
    cmd = "RETR {}".format(src)
    lines = []
    fd = open(path, 'w', encoding='latin1')
    def to_buffer(line):
        lines.append(line)
    ftp.retrlines(cmd, to_buffer)
    fd.write('\n'.join(lines))
    fd.close()
    with open(path, 'rb') as f:
        contents = f.read()
    return contents

def store_content(ftp, username, password, fp, src):
    cmd = "STOR {}".format(src)
    ftp.storlines(cmd, fp)

def modify_vms_file_content(host, username, password, src, callback=None):
    ftp = VMSFTP(host)
    ftp.encoding = 'latin1'
    ftp.login(username, password)
    with tempfile.TemporaryDirectory() as temp:
        path_origin = os.path.join(temp, 'downloaded.adl')
        content = get_content(ftp, username, password, src, path_origin)
        if callback is not None:
            content = callback(content)
        path = os.path.join(temp, 'toto.adl')
        with open(path, 'wb') as f:
            f.write(content)
        with open(path, 'rb') as f:
            store_content(ftp, username, password, f, src)
    ftp.close()


def remove_carriage_return(content):
    content = content.decode(encoding='latin1')
    lines = []
    for line in content.splitlines():
        lines.append(line)
    content = '\n'.join(lines)
    content = content.encode(encoding='latin1')
    return content


def cr_remover(version, path):

    ctx = settings.Context(version)

    modify_vms_file_content(ctx.hostname, ctx.username, ctx.password, path, callback=remove_carriage_return)

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    elif request.META.get('HTTP_X_REAL_IP'):
        ip = request.META.get('HTTP_X_REAL_IP')
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def add_new_record(request, version, path, status):
    ts = datetime.datetime.now()
    ip = get_client_ip(request)
    pr = models.PatchRecord(time=ts,
                            version=version,
                            path=path,
                            status=status,
                            ip=ip)
    pr.save()
