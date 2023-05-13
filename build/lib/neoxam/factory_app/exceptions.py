# -*- coding: utf-8 -*-

class TaskNotRunnable(Exception):
    def __init__(self, task):
        self.task = task
