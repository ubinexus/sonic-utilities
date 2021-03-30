import unittest
import os
from imp import load_source
load_source('generic_update', \
    os.path.join(os.path.dirname(__file__), '..', 'config', 'generic_update.py'))
import generic_update

# TODO: Add unit-tests
class Test(unittest.TestCase):
    pass
