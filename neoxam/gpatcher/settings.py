# -*- coding: utf-8 -*-
PAGINATION = 10

class SectionNames:
    GLOBAL = "GLOBAL"

class OptionNames:
    HOSTNAME = "HOSTNAME"
    USERNAME = "USERNAME"
    PASSWORD = "PASSWORD"

config = {
    SectionNames.GLOBAL:{
        OptionNames.HOSTNAME: "venus",
        "GP2009": "GP2009_CONFIG",
        "GP2006": "GP2006_CONFIG",
        "GP2016": "GP2016_CONFIG",
        "GP710": "GP710_CONFIG"},
    "GP2006_CONFIG": {
        OptionNames.USERNAME: "gp2006s",
        OptionNames.PASSWORD: "Alambra9"},
    "GP2009_CONFIG": {
        OptionNames.USERNAME: "gp2009s",
        OptionNames.PASSWORD: "Alambra9"},
    "GP2016_CONFIG": {
        OptionNames.USERNAME: "gp2016s",
        OptionNames.PASSWORD: "Alambra9"},
    "GP710_CONFIG": {
        OptionNames.USERNAME: "gp710s",
        OptionNames.PASSWORD: "Alambra9"},
    }

class Context:

    def __init__(self, version):
        self._cfg = config
        self._version = version
        

    @property
    def section(self):
        return self._cfg[SectionNames.GLOBAL][self._version]

    @property
    def hostname(self):
        return self._cfg[SectionNames.GLOBAL][OptionNames.HOSTNAME]

    @property
    def username(self):
        return self._cfg[self.section][OptionNames.USERNAME]

    @property
    def password(self):
        return self._cfg[self.section][OptionNames.PASSWORD]
