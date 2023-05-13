#! /usr/bin/env python
# -*- coding:utf-8 -*-

import datetime

GP_TRUNK_URL = "https://access.my-nx.com/svn/viewvc/gp/trunk"
FILTERING_THRESHOLD = datetime.timedelta(hours=72)
STARTING_REVISION = 150789
FROM_VERSION = 'gp2006'
TO_VERSION = 'gp2009'
RECORD_LOCK = 'backport.record'
PAGINATION = 10
