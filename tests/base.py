import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.core import config as config_module

# Deterministic test defaults.
os.environ["TEST_MODE"] = "1"
os.environ["RATE_LIMIT_ENABLED"] = "0"


class BaseAPITestCase(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmp_dir.name) / "test_rag.db"
        os.environ["RAG_DB_PATH"] = str(db_path)

        # Refresh settings so env updates are applied per test.
        config_module.settings = config_module.Settings()

        from app.main import create_app

        self.client = TestClient(create_app())

    def tearDown(self):
        self.client.close()
        self.tmp_dir.cleanup()

    def create_sample_project(self) -> Path:
        project_dir = Path(self.tmp_dir.name) / "sample_project"
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "math_utils.py").write_text(
            """
def add(a, b):
    return a + b

class Calculator:
    def divide(self, a, b):
        if b == 0:
            raise ZeroDivisionError("division by zero")
        return a / b
""".strip(),
            encoding="utf-8",
        )
        return project_dir
