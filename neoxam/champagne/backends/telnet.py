# -*- coding: utf-8 -*-
import logging
import telnetlib
import time

log = logging.getLogger(__name__)


class TelnetBackend(object):
    SETLF = 'set file/ATTR=RFM=STMLF /prot=W=R '

    def __init__(self, host, user, passwd, cwd, timeout=60, encoding='latin1', debug=0):
        self.host = host
        self.user = user
        self.passwd = passwd
        self.timeout = timeout
        self.encoding = encoding
        self.cwd = cwd
        self.debug = debug
        self.cx = None

    def initialize(self):
        self.cx = telnetlib.Telnet(self.host, timeout=self.timeout)
        self.cx.set_debuglevel(self.debug)
        self._read_until_write_ln('Username: ', self.user)
        self._read_until_write_ln('Password: ', self.passwd)
        self._write_ln('set term/vt100')
        self._read_until_vms_prompt()
        self._write_ln('set def [.%s]' % self.cwd.replace('/', '.'))
        self._read_until_vms_prompt()

    def compile(self, procedure_name, basename, timeout=15 * 60):
        echo = 'this is the end, my only friend, the end'
        self._write_ln('magnum')
        self._write_ln('terminal line.length 132')
        self._write_ln('compile %s from file "%s" no warn' % (procedure_name, basename))
        self._write_ln('yes')  # answer yes if as text override
        self._write_ln('quit')
        self._write_ln('write sys$output "%s"' % echo)
        # wait the ouput
        output = self.cx.expect(
            [echo.encode(self.encoding), 'Contact your MAGNUM Representative'.encode(self.encoding)],
            timeout,
        )[-1].decode(self.encoding).replace('\x00', '').replace('\x1b', '')
        output += self._read_until_vms_prompt()
        output = output.split('3.0>>')[0]
        return output

    def set_lf(self, basename):
        log.info('setlf on %s', basename)
        self._write_ln(self.SETLF + basename)
        self._read_until_vms_prompt()
        # Getting the prompt does not mean that setlf is done T_T
        # Can be an issue if try to download the file directly after
        time.sleep(2)

    def _read_until(self, msg, timeout=None):
        encoded_msg = msg.encode(self.encoding)
        output = self.cx.read_until(encoded_msg, timeout).decode(self.encoding)
        if msg not in output:
            raise ValueError('%s expected in %s' % (msg, output))
        return output

    def _write_ln(self, msg):
        msg_n = (msg + '\r').encode(self.encoding)
        self.cx.write(msg_n)

    def _read_until_vms_prompt(self, timeout=None):
        return self._read_until('$ ', timeout)

    def _read_until_write_ln(self, msg, value):
        output = self._read_until(msg)
        self._write_ln(value)
        return output

    def close(self):
        self._write_ln('logout')
        self.cx.close()
        self.cx = None
