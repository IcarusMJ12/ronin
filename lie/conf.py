# Copyright (c) 2011 Igor Kaplounenko.
# Licensed under the Open Software License version 3.0.

import ConfigParser

class Conf(ConfigParser.SafeConfigParser):
    conf=None

    def __init__(self, f, defaults=None):
        if f:
            ConfigParser.SafeConfigParser.__init__(self, defaults)
            self.read(f)
    
    @classmethod
    def getConf(self):
        if not Conf.conf:
            raise "Conf not initialized."
        return Conf.conf

    @classmethod
    def load(self, f, defaults=None):
        if Conf.conf is not None:
            raise "Conf already loaded."
        if f is None:
            raise "Configuration filename is required."
        Conf.conf = Conf(f, defaults)
