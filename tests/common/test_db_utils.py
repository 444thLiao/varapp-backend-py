#!/usr/bin/env python3

import unittest
from varapp.common.db_utils import *
from varapp.models.users import VariantsDb
from django.core.cache import caches
from django.conf import settings
import django.test

DB_TEST = settings.DB_TEST
TEST_DB_PATH = settings.GEMINI_DB_PATH


#@unittest.skip('')
class TestManageDbsUtils(django.test.TestCase):
    def test_is_on_disk(self):
        self.assertTrue(is_on_disk(DB_TEST, TEST_DB_PATH))

    def test_db_name_from_filename(self):
        self.assertEqual(db_name_from_filename("asdf.db"), "asdf")
        self.assertEqual(db_name_from_filename("asdf.db", "xxx"), "xxx")
        self.assertEqual(db_name_from_filename("aaa/asdf.db"), "asdf")

    def test_vdb_full_path(self):
        vdb = VariantsDb.objects.get(name='test', filename=DB_TEST, is_active=1)
        vdb_path = vdb_full_path(vdb)
        test_path = os.path.join(TEST_DB_PATH, DB_TEST)
        self.assertTrue(os.path.samefile(vdb_path, test_path))

    def test_add_db_to_settings__and_remove(self):
        self.assertNotIn('asdf', settings.DATABASES)
        add_db_to_settings('asdf', 'asdf.db', 'dir')
        self.assertIn('asdf', settings.DATABASES)
        self.assertIn('asdf', connections.databases)
        self.assertEqual(settings.DATABASES.get('asdf')['NAME'], 'dir/asdf.db')
        remove_db_from_settings('asdf')
        self.assertNotIn('asdf', settings.DATABASES)
        self.assertNotIn('asdf', connections.databases)

    def test_remove_db_from_cache(self):
        cache = caches['redis']
        gen_service_cache = caches['genotypes_service']
        cache.set('stats:xx:test:1', 22)
        cache.set('gen:xx:test:1', 22)
        gen_service_cache.set('xx', 22)
        self.assertIn('stats:xx:test:1', cache.keys('stats:*'))
        self.assertIn('gen:xx:test:1', cache.keys('gen:*'))
        self.assertIn('xx', gen_service_cache)
        remove_db_from_cache('xx')
        self.assertNotIn('stats:xx:test:1', cache.keys('stats:*'))
        self.assertNotIn('gen:xx:test:1', cache.keys('gen:*'))
        self.assertNotIn('xx', gen_service_cache)

    def test_remove_db(self):
        vdb = VariantsDb.objects.create(name='fff', filename='fff.db', location=TEST_DB_PATH, is_active=1)
        cache = caches['redis']
        cache.set('stats:fff:test:2', 33)
        settings.DATABASES[vdb.name] = 33
        connections.databases[vdb.name] = 33
        remove_db(vdb)
        self.assertNotIn('fff', settings.DATABASES)
        self.assertNotIn('fff', connections.databases)
        self.assertEqual(len(cache.keys('stats:fff:test:*')), 0)

    def test_is_test_vdb(self):
        vdb = VariantsDb.objects.get(filename=DB_TEST, is_active=1)
        self.assertTrue(is_test_vdb(vdb))
        vdb.filename = 'does_not_exist'
        self.assertFalse(is_test_vdb(vdb))
        vdb2 = VariantsDb(name='test', filename='asdf.db')
        self.assertFalse(is_test_vdb(vdb2))

    @unittest.skip("How to test that? Both ctime and timestamp are rounded to the second")
    def test_is_newer(self):
        """Create a file, then a VariantsDb, and compare timestamps."""
