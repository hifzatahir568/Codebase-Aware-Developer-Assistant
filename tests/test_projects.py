from base import BaseAPITestCase


class ProjectRouteTests(BaseAPITestCase):
    def test_register_index_ask_flow(self):
        project_dir = self.create_sample_project()
        register = self.client.post(
            "/projects/register",
            json={"project_path": str(project_dir), "name": "Demo"},
        )
        self.assertEqual(register.status_code, 200)
        project_id = register.json()["project_id"]

        index = self.client.post(f"/projects/{project_id}/index")
        self.assertEqual(index.status_code, 200)
        self.assertGreater(index.json()["chunks_indexed"], 0)

        ask = self.client.post(
            f"/projects/{project_id}/ask",
            json={"question": "What functions are in this project?", "top_k": 3, "max_context_chars": 1500},
        )
        self.assertEqual(ask.status_code, 200)
        payload = ask.json()
        self.assertTrue(payload["answer"])
        self.assertIsInstance(payload["citations"], list)

    def test_empty_question_validation(self):
        project_dir = self.create_sample_project()
        register = self.client.post(
            "/projects/register",
            json={"project_path": str(project_dir), "name": "Demo"},
        )
        project_id = register.json()["project_id"]
        self.client.post(f"/projects/{project_id}/index")

        ask = self.client.post(
            f"/projects/{project_id}/ask",
            json={"question": "   ", "top_k": 2, "max_context_chars": 1000},
        )
        self.assertEqual(ask.status_code, 400)
        self.assertIn("Question is required", ask.json().get("detail", ""))
