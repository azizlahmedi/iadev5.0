# -*- coding: utf-8 -*-

class NoSuchSprint(Exception):
    def __init__(self, sprint_id):
        super(NoSuchSprint, self).__init__()
        self.sprint_id = sprint_id
