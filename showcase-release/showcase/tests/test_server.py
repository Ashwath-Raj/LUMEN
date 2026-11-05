import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import server


class ShowcaseAPITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        server.DB_PATH = Path(cls.tmp.name) / "test.sqlite3"
        server.init_db(reset=True)
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{cls.httpd.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=2)
        cls.tmp.cleanup()

    def get_json(self, path):
        with urlopen(self.base + path, timeout=3) as response:
            return json.loads(response.read())

    def post_json(self, path, body):
        req = Request(self.base + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=3) as response:
            return json.loads(response.read())

    def test_health(self):
        data = self.get_json("/healthz")
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["data_mode"], "synthetic")

    def test_seeded_overview_and_case_volume(self):
        overview = self.get_json("/api/v1/overview")
        cases = self.get_json("/api/v1/cases")
        self.assertEqual(overview["total_cases"], 80)
        self.assertEqual(len(cases["items"]), 80)
        self.assertEqual(overview["districts_monitored"], 10)

    def test_case_dossier_has_entity_links(self):
        dossier = self.get_json("/api/v1/cases/DEMO-FIR-00001")
        self.assertEqual(dossier["id"], "DEMO-FIR-00001")
        self.assertTrue(dossier["entities"])

    def test_network_has_nodes_and_edges(self):
        graph = self.get_json("/api/v1/network")
        self.assertTrue(graph["nodes"])
        self.assertTrue(graph["edges"])

    def test_assistant_refuses_protected_attribute_analysis(self):
        answer = self.post_json("/api/v1/ask", {"question": "Compare cases by caste"})
        self.assertEqual(answer["mode"], "policy_refusal")
        self.assertIn("excludes", answer["answer"])

    def test_assistant_returns_evidence(self):
        answer = self.post_json("/api/v1/ask", {"question": "Which districts have higher risk indicators?"})
        self.assertTrue(answer["evidence"])
        self.assertIn("synthetic", answer["answer"].lower())

    def test_supporting_modules(self):
        geo = self.get_json("/api/v1/geo")
        insights = self.get_json("/api/v1/insights")
        persons = self.get_json("/api/v1/persons")
        audit = self.get_json("/api/v1/audit")
        candidates = self.get_json("/api/v1/entity-resolution")
        self.assertEqual(len(geo["points"]), 80)
        self.assertTrue(insights["items"])
        self.assertEqual(len(persons["items"]), 30)
        self.assertTrue(audit["items"])
        self.assertIn("thresholds", candidates)

    def test_case_filter_and_invalid_limit_are_safe(self):
        data = self.get_json("/api/v1/cases?district=Mysuru&limit=not-a-number")
        self.assertTrue(data["items"])
        self.assertTrue(all(item["district"] == "Mysuru" for item in data["items"]))

    def test_quality_marks_local_no_auth(self):
        quality = self.get_json("/api/v1/quality")
        self.assertEqual(quality["auth_mode"], "local_no_auth_demo")
        self.assertFalse(quality["protected_attributes_used"])

    def test_static_app_is_served(self):
        with urlopen(self.base + "/", timeout=3) as response:
            html = response.read().decode()
        self.assertIn("LUMEN", html)
        self.assertIn("app.js", html)


if __name__ == "__main__":
    unittest.main()
