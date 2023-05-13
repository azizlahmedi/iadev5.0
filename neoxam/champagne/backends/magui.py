# -*- coding: utf-8 -*-
import os
import subprocess
import tempfile

from neoxam.champagne import settings


class MaguiBackend(object):
    def __init__(self, support_home):
        self.support_home = support_home

    def extract(self, procedure_name, mag_dir, magui_dir):
        with tempfile.TemporaryDirectory() as temp:
            config_path = os.path.join(temp, 'mrun.conf')
            error_path = os.path.join(self.support_home, 'share', 'zermagn.xml')
            with open(config_path, 'w', encoding='utf-8') as fd_config:
                fd_config.write('''
SCHEMA=%s
MAGNUM_ERROR_CATALOG=%s
MAGNUM_DEFAULT_DIRECTORY=%s
MAGNUM_MAGUI_DIRECTORY=%s
MAGNUM_PYTHON_DBURI=sqlite://empty.db
        ''' % (settings.SCHEMA_NAME, error_path, mag_dir, magui_dir))
            env = os.environ.copy()
            env['LD_LIBRARY_PATH'] = os.path.join(self.support_home, 'lib') \
                                     + os.pathsep + env.get('LD_LIBRARY_PATH', '')
            env['PATH'] = os.path.join(self.support_home, 'bin') \
                          + os.pathsep + env.get('PATH', '')
            env['PYTHONHOME'] = self.support_home
            env['LANG'] = 'en_us.UTF-8'
            magui_path = os.path.join(magui_dir, procedure_name.replace('.', '_').lower() + '.magui')
            command = [
                os.path.join(self.support_home, 'bin', 'magui-extract'),
                '-f', config_path,
                '-O', magui_dir,
                procedure_name,
            ]
            output = subprocess.check_output(command, env=env, stderr=subprocess.STDOUT)
            if not os.path.isfile(magui_path):
                raise ValueError('failed to generate magui:\n' + output.decode('utf-8', 'replace'))
            return magui_path
