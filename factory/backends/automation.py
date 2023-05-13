# -*- coding: utf-8 -*-
import requests

from factory import consts


class AutomationBackend(object):
    def __init__(self, deliver_url, requests_handler=requests):
        self.deliver_url = deliver_url
        self.requests_handler = requests_handler

    def deliver(self, schema_version, procedure_name, revision, resource_revision, url, technical_tests):
        if self.deliver_url:
            tests = {}
            for technical_test_key in consts.TECHNICAL_TEST_KEYS:
                tests[technical_test_key] = {
                    'result': 'pass',
                    'log': 'Not implemented.'
                }
            for technical_test in technical_tests:
                if technical_test.key in consts.TECHNICAL_TEST_KEYS:
                    tests[technical_test.key] = {
                        'result': technical_test.result_as_str,
                        'log': technical_test.log,
                    }
            data = {
                'schema': {
                    'version': schema_version,
                    'name': consts.SCHEMA_NAME,
                },
                'procedure': {
                    'name': procedure_name,
                    'revision': revision,
                    'resource_revision': resource_revision,
                },
                'url': url,
                'tests': tests,
            }
            self.requests_handler.post(self.deliver_url, json=data).raise_for_status()
