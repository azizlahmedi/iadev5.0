# -*- coding: utf-8 -*-
from collections import OrderedDict
import json
import requests


def push_runtime(url, user_name, ip_address, port_number):
    payload = OrderedDict()
    payload['user_name'] = user_name
    payload['ip_address'] = ip_address
    payload['port_number'] = port_number

    response = requests.post(url, data=json.dumps(payload))
    response.raise_for_status()


def push_http_server(url, ip_address, port_number):
    payload = OrderedDict()
    payload['ip_address'] = ip_address
    payload['port_number'] = port_number

    response = requests.post(url, data=json.dumps(payload))
    response.raise_for_status()


def put_http_server(url, ip_address, port_number):
    payload = OrderedDict()
    payload['ip_address'] = ip_address
    payload['port_number'] = port_number

    response = requests.put(url, data=json.dumps(payload))
    response.raise_for_status()


def get_http_server(url, ip_address):
    url = url + ip_address +'/'
    response = requests.get(url)
    content = json.loads(response.content.decode(encoding='utf-8'))
    print(content)
    response.raise_for_status()


def put_runtime(url, user_name, ip_address, port_number):
    payload = OrderedDict()
    payload['user_name'] = user_name
    payload['ip_address'] = ip_address
    payload['port_number'] = port_number

    response = requests.put(url, data=json.dumps(payload))
    response.raise_for_status()


def get_runtime(url, user_name):
    url = url + user_name + '/'
    response = requests.get(url)
    content = json.loads(response.content.decode(encoding='utf-8'))
    print(content)
    response.raise_for_status()


def test_1():
    push_runtime('http://127.0.0.1:8000/webintake/api/user/push/', 'neoxam', '10.33.23.123',
        10000)


    push_runtime('http://127.0.0.1:8000/webintake/api/user/push/', 'neoxam', '10.33.23.123',
        10000)


    put_runtime('http://127.0.0.1:8000/webintake/api/user/push/', 'hao.hu', '10.33.23.123',
        8888)


    push_runtime('http://127.0.0.1:8000/webintake/api/user/push/', 'gpform1', '10.33.23.123',
        10000)

    get_runtime('http://127.0.0.1:8000/webintake/api/user/get/', 'hao.hu')


def test_2():
    push_http_server('http://127.0.0.1:8000/webintake/api/http_server/push/', '10.33.23.123', 8080)

    push_http_server('http://127.0.0.1:8000/webintake/api/http_server/push/', '10.33.23.123', 8000)

    put_http_server('http://127.0.0.1:8000/webintake/api/http_server/push/', '10.33.23.123', 9999)

    push_http_server('http://127.0.0.1:8000/webintake/api/http_server/push/', '10.33.23.123', 9998)

    get_http_server('http://127.0.0.1:8000/webintake/api/http_server/get/', '10.33.23.123')

if __name__ == '__main__':
    test_1()
    test_2()
