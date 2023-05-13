# -*- coding: utf-8 -*-
import ftplib


class FTPBackend(object):
    def __init__(self, host, user, passwd, cwd):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.cwd = cwd
        self.cx = None

    def initialize(self):
        self.cx = ftplib.FTP(host=self.host, user=self.user, passwd=self.passwd)
        self.cx.cwd(self.cwd)

    def put(self, local_path, remote_path):
        with open(local_path, 'rb') as fd:
            self.cx.storlines('STOR %s' % remote_path, fd)

    def get(self, remote_path, local_path):
        with open(local_path, 'wb') as fd:
            self.cx.retrbinary('RETR %s' % remote_path, fd.write)

    def exists(self, remote_path):
        try:
            self.cx.nlst(remote_path)
            return True
        except Exception:
            return False

    def close(self):
        self.cx.close()
        self.cx = None

    def delete(self, remote_path):
        self.cx.delete('%s;*' % remote_path)
