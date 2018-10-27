#!/usr/local/bin/python

from nose import with_setup
from os import environ

LIBARARY_PATH='pygdbcli'

import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
pygdbsdir = os.path.join(parentdir, LIBRARY_PATH)
sys.path.insert(0, pygdbsdir)

from ClientTcp import ClientTcp

class TestCli:

    @classmethod
    def setup_class(self):
        pass

    def test_can_access_gdb(self):
        assert 1 == 0
