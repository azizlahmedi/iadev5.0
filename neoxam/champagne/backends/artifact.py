# -*- coding: utf-8 -*-
import hashlib

import requests


class ArtifactBackend(object):
    def __init__(self, url, user, passwd):
        self.url = url
        self.user = user
        self.passwd = passwd

    def publish(self, procedure_name, version, filename):
        artifact_url = '{url}/{procedure_name}/{version}/{procedure_name}-{version}.tgz;version={version}'.format(
            url=self.url,
            procedure_name=procedure_name,
            version=version,
        )
        md5 = hashlib.md5(open(filename, mode='rb').read()).hexdigest()
        sha1 = hashlib.sha1(open(filename, mode='rb').read()).hexdigest()
        headers = {
            'X-Checksum-Md5': md5,
            'X-Checksum-Sha1': sha1,
        }
        with open(filename, 'rb') as artifact_binary:
            response = requests.put(artifact_url, data=artifact_binary, auth=(self.user, self.passwd), headers=headers)
            if 400 <= response.status_code < 600:
                raise requests.HTTPError(str(response.status_code) + '\n' + response.text)
