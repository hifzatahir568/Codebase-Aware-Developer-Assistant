from fastapi.testclient import TestClient

from app.core import config as config_module
from base import BaseAPITestCase


class RateLimitTests(BaseAPITestCase):
    def test_rate_limit_enforced(self):
        config_module.settings.rate_limit_enabled = True
        config_module.settings.rate_limit_per_minute = 2

        from app.main import create_app

        client = TestClient(create_app())
        project_dir = self.create_sample_project()

        r1 = client.post("/projects/register", json={"project_path": str(project_dir), "name": "x"})
        r2 = client.post("/projects/register", json={"project_path": str(project_dir), "name": "x"})
        r3 = client.post("/projects/register", json={"project_path": str(project_dir), "name": "x"})

        self.assertIn(r1.status_code, {200, 400})
        self.assertIn(r2.status_code, {200, 400})
        self.assertEqual(r3.status_code, 429)

        client.close()
        config_module.settings.rate_limit_enabled = False
        config_module.settings.rate_limit_per_minute = 60
