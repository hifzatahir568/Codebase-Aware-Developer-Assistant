from base import BaseAPITestCase


class HealthTests(BaseAPITestCase):
    def test_health(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("status"), "running")
