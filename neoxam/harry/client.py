# -*- coding: utf-8 -*-
import socket
from collections import OrderedDict

import requests


def push(url, path, procedure, session_id, version):
    payload = OrderedDict()
    payload['procedure'] = procedure
    payload['hostname'] = socket.gethostname()
    payload['session_id'] = session_id
    payload['version'] = version

    with open(path, encoding='utf-8') as fd:
        files = {'file': ('trad.csv', fd.read(), 'text/csv')}

        response = requests.post(url, data=payload, files=files)
        response.raise_for_status()


# push('http://127.0.0.1:8000/harry/api/v1/push/', '/workspace/src/sandbox/neoxam/neoxam/harry/test.data',
#      'newport_gestab_lisanx', 'a', 'b')
