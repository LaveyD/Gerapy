import importlib
import os
import unittest
from unittest.mock import patch


class DatabaseSettingsTests(unittest.TestCase):
    module_name = 'backend.server.settings'

    def load_settings(self):
        module = importlib.import_module(self.module_name)
        return importlib.reload(module)

    def test_database_defaults_to_postgresql(self):
        with patch.dict(os.environ, {}, clear=True):
            settings = self.load_settings()
            self.assertEqual(
                settings.DATABASES['default']['ENGINE'],
                'django.db.backends.postgresql'
            )

    def test_sqlite_compatibility_mode(self):
        with patch.dict(os.environ, {'GERAPY_SQLITE_COMPAT': 'true'}, clear=True):
            settings = self.load_settings()
            self.assertEqual(
                settings.DATABASES['default']['ENGINE'],
                'django.db.backends.sqlite3'
            )
