# -*- coding: utf-8 -*-
"""
    tests.nmea.server
    ~~~~~~~~~~~~~~~~~~~~~

    Test the nmea.server module.

    :license: APLv2, see LICENSE for more details.
"""

import unittest

from nmea import server


def dummy1(): pass
def dummy2(): pass

def assertServerClean(self):
    self.assertIsNone(self.server.missing_handler)
    self.assertIsNone(self.server.message_pre_handler)
    self.assertIsNone(self.server.message_post_handler)
    self.assertIsNone(self.server.error_handler)
    self.assertIsNone(self.server.bad_checksum_message_handler)
    self.assertIsNone(self.server.connection_context_creator)

class TestStringMethods(unittest.TestCase):
    server = server.NMEAServer()

    def test_add_message_handler(self):
        assertServerClean(self)
        with self.assertRaises(KeyError):
            self.server.message_handlers['RXTST']
        self.server.add_message_handler('RXTST', dummy1)
        self.assertEqual(self.server.message_handlers['RXTST'], dummy1)
        self.assertNotEqual(self.server.message_handlers['RXTST'], dummy2)
        self.server.add_message_handler('RXTST', None)
        self.assertIsNone(self.server.message_handlers['RXTST'])
        assertServerClean(self)

    def test_add_prehandler(self):
        assertServerClean(self)
        self.server.add_prehandler(dummy1)
        self.assertEqual(self.server.message_pre_handler, dummy1)
        self.assertNotEqual(self.server.message_pre_handler, dummy2)
        self.server.add_prehandler(None)
        self.assertIsNone(self.server.message_pre_handler)
        assertServerClean(self)

    def test_add_posthandler(self):
        assertServerClean(self)
        self.server.add_posthandler(dummy1)
        self.assertEqual(self.server.message_post_handler, dummy1)
        self.assertNotEqual(self.server.message_post_handler, dummy2)
        self.server.add_posthandler(None)
        self.assertIsNone(self.server.message_post_handler)
        assertServerClean(self)

    def test_add_unknown_message(self):
        assertServerClean(self)
        self.server.add_unknown_message(dummy1)
        self.assertEqual(self.server.missing_handler, dummy1)
        self.assertNotEqual(self.server.missing_handler, dummy2)
        self.server.add_unknown_message(None)
        self.assertIsNone(self.server.missing_handler)
        assertServerClean(self)

    def test_add_context_creator(self):
        assertServerClean(self)
        self.server.add_context_creator(dummy1)
        self.assertEqual(self.server.connection_context_creator, dummy1)
        self.assertNotEqual(self.server.connection_context_creator, dummy2)
        self.server.add_context_creator(None)
        self.assertIsNone(self.server.connection_context_creator)
        assertServerClean(self)

    def test_add_bad_checksum_handler(self):
        assertServerClean(self)
        self.server.add_bad_checksum_handler(dummy1)
        self.assertEqual(self.server.bad_checksum_message_handler, dummy1)
        self.assertNotEqual(self.server.bad_checksum_message_handler, dummy2)
        self.server.add_bad_checksum_handler(None)
        self.assertIsNone(self.server.bad_checksum_message_handler)
        assertServerClean(self)

    def test_add_error_handler(self):
        assertServerClean(self)
        self.server.add_error_handler(dummy1)
        self.assertEqual(self.server.error_handler, dummy1)
        self.assertNotEqual(self.server.error_handler, dummy2)
        self.server.add_error_handler(None)
        self.assertIsNone(self.server.error_handler)
        assertServerClean(self) 

if __name__ == '__main__':
    unittest.main()
