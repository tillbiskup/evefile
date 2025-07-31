import unittest

from evefile import evefile


class TestEveFile(unittest.TestCase):
    def setUp(self):
        self.eve_file = evefile.EveFile()

    def test_instantiate_class(self):
        pass
