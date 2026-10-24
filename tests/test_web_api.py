"""Unit tests for ZYRA Web Dashboard API."""
import unittest
import json
from zyra.web.app import app
from zyra.safety import safety_guard

class TestWebAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        safety_guard._pending_action = None

    def tearDown(self):
        safety_guard._pending_action = None

    def test_index_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"FRIDAY", response.data)

    def test_status_endpoint(self):
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("assistant_name", data)
        self.assertIn("media_indexer_ready", data)
        self.assertIn("tts_enabled", data)

    def test_quick_actions_endpoint(self):
        response = self.client.get("/api/quick-actions")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertTrue(len(data) > 0)
        self.assertIn("category", data[0])

    def test_command_execution_api(self):
        payload = {"command": "help"}
        response = self.client.post("/api/command", json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertIn("Here is what I can do", data["response"])

    def test_empty_command(self):
        response = self.client.post("/api/command", json={"command": ""})
        self.assertEqual(response.status_code, 400)

    def test_confirmation_api(self):
        safety_guard.request_confirmation("test_act", "test description", lambda: "Success Executed")
        self.assertTrue(safety_guard.has_pending)

        # Confirm via API
        response = self.client.post("/api/confirm", json={"action": "yes"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["response"], "Success Executed")
        self.assertFalse(safety_guard.has_pending)

    def test_config_update_api(self):
        payload = {"tts_enabled": False, "tts_rate": 180}
        response = self.client.post("/api/config", json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertFalse(data["config"]["tts_enabled"])
        self.assertEqual(data["config"]["tts_rate"], 180)

if __name__ == "__main__":
    unittest.main()
