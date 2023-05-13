import os
import subprocess
import xml.etree.ElementTree as ET


class SubversionBackend(object):
    def __init__(self, user=None, passwd=None, svn_binary='svn', timeout=60):
        self.user = user
        self.passwd = passwd
        self.svn_binary = svn_binary
        self.timeout = timeout

    def execute(self, subcommand, args, auth=True):
        env = os.environ.copy()
        env['LANG'] = 'en_US.UTF-8'
        command = [
            self.svn_binary,
            # '--trust-server-cert', not available on neptune
        ]
        if auth:
            command.extend([
                '--non-interactive',
                '--no-auth-cache',
            ])
            if self.user:
                command.extend(['--username', self.user])
            if self.passwd:
                command.extend(['--password', self.passwd])
        command.append(subcommand)
        command.extend(args)
        return subprocess.check_output(command, stderr=subprocess.STDOUT, env=env, timeout=self.timeout).decode('utf-8')

    def checkout(self, url, path, revision=None):
        if os.path.exists(path):
            raise ValueError('checkout already exists: %s' % path)
        args = []
        if revision:
            args.extend(['-r', str(revision)])
        args.extend((url, path))
        self.execute('checkout', args)

    def safe_checkout(self, url, path, revision=None):
        try:
            self.checkout(url, path, revision=revision)
        except subprocess.CalledProcessError:
            return False
        return True

    def export(self, url, path, revision=None):
        if os.path.exists(path):
            raise ValueError('export already exists: %s' % path)
        d = os.path.dirname(path)
        if not os.path.exists(d):
            os.makedirs(d)
        args = []
        if revision:
            args.extend(['-r', str(revision)])
        args.extend((url, path))
        self.execute('export', args)

    def safe_export(self, url, path, revision=None):
        try:
            self.export(url, path, revision=revision)
        except subprocess.CalledProcessError as e:
            return False
        return True

    def get_revisions(self, paths):
        revisions = {}
        args = ['--xml']
        args.extend(paths)
        raw_xml = self.execute('info', args, auth=False)
        for entry in ET.fromstring(raw_xml):
            found = False
            path = entry.get('path')
            for child in entry:
                if child.tag == 'commit':
                    if found:
                        raise ValueError('multiple commit tag for %s' % path)
                    revision = int(child.get('revision'))
                    revisions[path] = revision
                    found = True
            if not found:
                raise ValueError('commit tag is missing for %s' % path)
        return revisions

    def get_head_revision(self, url):
        output = self.execute('info', args=(url,))
        try:
            return int(output.split('Revision: ')[1].split('\n')[0])
        except:
            raise ValueError('failed to get head revision from:\n' + output)
