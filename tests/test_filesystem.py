from base import BaseAPITestCase


class FilesystemTests(BaseAPITestCase):
    def test_filesystem_dirs_endpoint(self):
        response = self.client.get("/filesystem/dirs")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("path", payload)
        self.assertIn("directories", payload)
