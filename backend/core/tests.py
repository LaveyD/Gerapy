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

    def test_sqlite_engine_override(self):
        with patch.dict(os.environ, {'GERAPY_DB_ENGINE': 'sqlite'}, clear=True):
            settings = self.load_settings()
            self.assertEqual(
                settings.DATABASES['default']['ENGINE'],
                'django.db.backends.sqlite3'
            )

    def test_postgresql_params_from_env(self):
        with patch.dict(os.environ, {
            'GERAPY_DB_NAME': 'gerapy_test',
            'GERAPY_DB_USER': 'gerapy_user',
            'GERAPY_DB_PASSWORD': 'gerapy_pass',
            'GERAPY_DB_HOST': 'db.internal',
            'GERAPY_DB_PORT': '5433',
        }, clear=True):
            settings = self.load_settings()
            self.assertEqual(settings.DATABASES['default']['NAME'], 'gerapy_test')
            self.assertEqual(settings.DATABASES['default']['USER'], 'gerapy_user')
            self.assertEqual(settings.DATABASES['default']['PASSWORD'], 'gerapy_pass')
            self.assertEqual(settings.DATABASES['default']['HOST'], 'db.internal')
            self.assertEqual(settings.DATABASES['default']['PORT'], '5433')

    def test_invalid_engine_falls_back_to_postgresql(self):
        with patch.dict(os.environ, {'GERAPY_DB_ENGINE': 'mysql'}, clear=True):
            settings = self.load_settings()
            self.assertEqual(
                settings.DATABASES['default']['ENGINE'],
                'django.db.backends.postgresql'
            )
