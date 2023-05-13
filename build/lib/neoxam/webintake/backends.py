# -*- coding: utf-8 -*-
import logging
import socket

from neoxam.webintake import consts, models

logger = logging.getLogger(__file__)


def check_connectivity(ip_addr, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(consts.check_connectivity_timeout)
        s.connect((ip_addr, port))
    except ConnectionError:
        return False
    except socket.timeout:
        return False
    else:
        return True
    finally:
        s.close()


def clean_up_users():
    to_delete = []
    for u in models.wUser.objects.all():
        ip_address = u.ip_address
        port = u.port_number
        if check_connectivity(ip_address, port):
            pass
        else:
            to_delete.append(u)
    for user in to_delete:
        logger.info("Clearing up user: {}.".format(str(user)))
        user.delete()
