# -*- coding: utf-8 -*-

import logging
from redis.exceptions import ConnectionError
import unittest
from unittest.mock import Mock
from store import Store
from tests.helper import cases


class TestStore(unittest.TestCase):
    store = Store()

    def setUp(self):
        logging.disable(logging.CRITICAL)
        self.store.connect()

    @cases([['1', [b'hi-tech', b'books']], ['2', [b'tv', b'cinema']]])
    def test_set_get(self, params):
        key, values = params
        self.store.set(key, *values)
        stored_values = self.store.get(key)
        self.assertEqual(sorted(values), sorted(stored_values))

    def test_get_key_not_exists(self):
        self.assertEqual(self.store.get('0'), set())

    @cases(
        [
            ['key', b'value'],
            ['1', b'12345'],
            ['12key', b'1v2a3l4u5e'],
        ]
    )
    def test_cache_set_get(self, params):
        key, value = params
        self.store.cache_set(key, value, 1)
        cached_value = self.store.cache_get(key)
        self.assertEqual(value, cached_value)

    def test_lost_connection(self):
        self.store.client = Mock(
            sadd=Mock(side_effect=ConnectionError),
            smembers=Mock(side_effect=ConnectionError),
            set=Mock(side_effect=ConnectionError),
            get=Mock(side_effect=ConnectionError),
        )

        with self.assertRaises(ConnectionError):
            self.store.set('foo', 'foobar')
            self.store.get('foo')

        self.assertIsNone(self.store.cache_set('foo', 'foobar', 5))
        self.assertIsNone(self.store.cache_get('foo'))

    def tearDown(self):
        logging.disable(logging.NOTSET)
        self.store.client.flushdb()
        self.store.close()
