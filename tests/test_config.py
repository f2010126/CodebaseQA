import unittest
from pathlib import Path
from app.config import settings, logger


class TestConfig(unittest.TestCase):

    def test_settings_instance(self):
        from pydantic_settings import BaseSettings
        self.assertIsInstance(settings, BaseSettings)

    def test_debug_flag_type(self):

        self.assertIsInstance(settings.debug, bool)

    def test_paths_are_path_objects(self):

        self.assertIsInstance(settings.vectorstore_root, Path)
        self.assertIsInstance(settings.project_root, Path)

    def test_path_logic(self):

        # vectorstore_root should be a child of project_root
        self.assertEqual(settings.vectorstore_root,
                         settings.project_root / "vectorstore")

    def test_logger_exists(self):

        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, "app.config")


if __name__ == "__main__":
    unittest.main()
