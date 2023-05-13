# -*- coding: utf-8 -*-
import logging
import os
import uuid
import xml.etree.ElementTree as ET

import paramiko
import requests

log = logging.getLogger(__name__)


class WSBackend(object):
    def __init__(self, wsdl, host, user, passwd, cwd):
        self.wsdl = wsdl
        self.ns = wsdl.split('?')[0]
        self.host = host
        self.user = user
        self.passwd = passwd
        self.cwd = '.' + cwd.replace('/', '.')
        self.session_key = None

    def _send(self, body):
        envelope = '''<?xml version="1.0" encoding="UTF-8"?>
<SOAP-ENV:Envelope
  SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
  xmlns:SOAP-ENC="http://schemas.xmlsoap.org/soap/encoding/"
  xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance"
  xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
  xmlns:xsd="http://www.w3.org/1999/XMLSchema"
>
<SOAP-ENV:Body>
%s
</SOAP-ENV:Body>
</SOAP-ENV:Envelope>''' % body
        response = requests.request(
            'POST',
            self.wsdl,
            headers={'Content-Type': 'text/xml;charset=UTF-8',
                     'SOAPAction': 'sendMsg'},
            data=envelope,
        )
        response.raise_for_status()
        return ET.fromstring(response.text)

    def _search(self, elmt, name):
        if elmt.tag.split('}')[-1] == name:
            return elmt
        for child in elmt.getchildren():
            found = self._search(child, name)
            if found is not None:
                return found

    def _initialize_new_session(self, kill_previous):
        body = '''<ns1:initializeNewSession xmlns:ns1="{ns}" SOAP-ENC:root="1">
<v1 xsi:type="xsd:string">{host}</v1>
<v2 xsi:type="xsd:string">{user}</v2>
<v3 xsi:type="xsd:string">{passwd}</v3>
<v4 xsi:type="xsd:string">{cwd}</v4>
<v5 xsi:type="xsd:boolean">{kill_previous}</v5>
</ns1:initializeNewSession>
'''.format(ns=self.ns, host=self.host, user=self.user, passwd=self.passwd, cwd=self.cwd,
           kill_previous=kill_previous)
        root = self._send(body)
        elmt = self._search(root, 'initializeNewSessionReturn')
        return int(elmt.text)

    def initialize(self):
        self.session_key = self._initialize_new_session(False)
        if self.session_key < 0:
            self.session_key = self._initialize_new_session(True)
            if self.session_key < 0:
                raise ValueError('failed to initialize new session')
        self._create_env()

    def _create_env(self):
        body = '''<ns1:createEnv xmlns:ns1="{ns}" SOAP-ENC:root="1">
<v1 xsi:type="xsd:int">{session_key}</v1>
<v2 xsi:type="xsd:string">portefeuille</v2>
</ns1:createEnv>
        '''.format(ns=self.ns, session_key=self.session_key)
        self._send(body)

    def _compile(self, basename):
        body = '''<ns1:compile xmlns:ns1="{ns}" SOAP-ENC:root="1">
<v1 xsi:type="xsd:int">{session_key}</v1>
<v2 xsi:type="xsd:string">.bin</v2>
<v3 xsi:type="xsd:string">{basename}</v3>
<v4 xsi:type="xsd:int">2</v4>
<v5 xsi:type="xsd:boolean">False</v5>
<v6 SOAP-ENC:arrayType="xsd:anyType[0]" xsi:type="SOAP-ENC:Array">
</v6>
</ns1:compile>'''.format(ns=self.ns, session_key=self.session_key, basename=basename)
        root = self._send(body)
        return '\n'.join([elmt.text for elmt in self._search(root, 'multiRef').getchildren()])

    def start_compilation(self, basename):
        procedure_name = basename.split('.')[0].replace('_', '.').lower()
        log_basename = '%s.log' % uuid.uuid4()
        body = '''<ns1:startCompilation xmlns:ns1="{ns}" SOAP-ENC:root="1">
<v1 xsi:type="xsd:int">{session_key}</v1>
<v2 xsi:type="xsd:string">.bin</v2>
<v3 xsi:type="xsd:string">{basename}</v3>
<v4 xsi:type="xsd:string">{procedure_name}</v4>
<v5 xsi:type="xsd:int">2</v5>
<v6 xsi:type="xsd:boolean">False</v6>
<v7 SOAP-ENC:arrayType="xsd:anyType[0]" xsi:type="SOAP-ENC:Array">
</v7>
<v8 xsi:type="xsd:int">0</v8>
<v9 xsi:type="xsd:string">{log_basename}</v9>
</ns1:startCompilation>'''.format(ns=self.ns, session_key=self.session_key, basename=basename,
                                  procedure_name=procedure_name, log_basename=log_basename)
        self._send(body)
        return log_basename

    def wait_compilation(self):
        body = '''<ns1:waitCompilation xmlns:ns1="{ns}" SOAP-ENC:root="1">
<v1 xsi:type="xsd:int">{session_key}</v1>
<v2 xsi:type="xsd:int">{time}</v2>
</ns1:waitCompilation>
        '''.format(ns=self.ns, session_key=self.session_key, time=1000)
        root = self._send(body)
        elmt = self._search(root, 'waitCompilationReturn')
        return elmt.text == 'true'

    def set_lf(self, basename):
        body = '''<ns1:runSetLF xmlns:ns1="{ns}" SOAP-ENC:root="1">
<v1 xsi:type="xsd:int">{session_key}</v1>
<v2 xsi:type="xsd:string">.bin</v2>
<v3 xsi:type="xsd:string">{basename}</v3>
</ns1:runSetLF>'''.format(ns=self.ns, session_key=self.session_key, basename=basename)
        self._send(body)

    def compile(self, basename):
        output = self._compile(basename)
        return output

    def close(self):
        body = '''<ns1:closeSession xmlns:ns1="{ns}" SOAP-ENC:root="1">
<v1 xsi:type="xsd:int">{session_key}</v1>
</ns1:closeSession>'''.format(ns=self.ns, session_key=self.session_key)
        self._send(body)
        self.session_key = None


class WSLogBackend(object):
    def __init__(self, host, user, passwd, log_dir):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.log_dir = log_dir
        self.cx = None
        self.sftp = None

    def initialize(self):
        self.cx = paramiko.SSHClient()
        self.cx.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.cx.connect(self.host, username=self.user, password=self.passwd)
        self.sftp = self.cx.open_sftp()

    def close(self):
        self.cx.close()
        self.cx = None
        self.sftp = None

    def get_content(self, basename):
        try:
            with self.sftp.open(os.path.join(self.log_dir, basename), 'rb') as fd:
                return fd.read().decode('latin1', 'replace')
        except (FileNotFoundError, IOError):
            log.info('file not found: %s', basename)
            return ''

    def _ensure_no_error(self, procedure_name, content):
        if '===ABNORMAL-TERMINATION-OF-MAGNUM-COMPILATION===' in content \
                or '===TIMEOUT-COMPILATION-ABORTED===' in content \
                or '===COMPILATION-ABORTED===' in content \
                or ('INTERNAL ERROR' in content and 'Contact your MAGNUM Representative' in content \
                            and '%s Text Created.' % procedure_name.upper() not in content):
            raise ValueError('compilation failed:\n' + content)

    def check_completed(self, procedure_name, basename):
        content = self.get_content(basename)
        self._ensure_no_error(procedure_name, content)
        return '%s Text Created.' % procedure_name.upper() in content
