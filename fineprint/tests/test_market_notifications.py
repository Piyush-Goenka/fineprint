import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from fineprint.market_notifications import notification, post_slack
from fineprint.market_data import build


class MarketNotificationTests(unittest.TestCase):
    def test_router_stays_in_picker_without_a_model_rank(self):
        catalog = [{"id": "nvidia/switchyard", "name": "NVIDIA: Switchyard"}]
        snapshot = build(catalog, [], {}, {}, "2026-10-05T00:00:00Z")
        self.assertEqual(snapshot["rows"], [])
        self.assertEqual(snapshot["catalog"][0]["id"], "nvidia/switchyard")

    def test_new_model_and_repeat_refresh(self):
        previous = {"rows": [{"id": "old"}], "n_ranked": 1}
        current = {
            "rows": [
                {"id": "new", "label": "New Model", "rank": 1, "overall": 88.4},
                {"id": "old", "label": "Old Model", "rank": 2, "overall": 80.0},
            ],
            "n_ranked": 2,
        }
        count, message = notification(previous, current)
        self.assertEqual(count, 1)
        self.assertIn("New Model (#1, Index 88.4)", message)
        self.assertNotIn("Old Model (#2", message)
        count, _ = notification(current, current)
        self.assertEqual(count, 0)

    def test_slack_webhook_receives_test_message(self):
        received = []

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                received.append(json.loads(self.rfile.read(length)))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"ok")

            def log_message(self, *_):
                pass

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            current = {"rows": [{"id": "leader", "label": "Leader"}], "n_ranked": 1}
            count, message = notification(current, current, test=True)
            self.assertEqual(count, 0)
            post_slack(f"http://127.0.0.1:{server.server_port}/", message)
            self.assertEqual(received, [{"text": message}])
            self.assertIn("Slack delivery test", message)
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

    def test_flexprice_task_scores_adjust_overall_index_when_present(self):
        from fineprint.market_data import flexprice_task_score
        catalog = [
            {"id": "anthropic/claude-opus-5", "name": "Claude Opus 5", "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]}},
            {"id": "openai/gpt-6-astra", "name": "GPT-6 Astra", "architecture": {"input_modalities": ["text"], "output_modalities": ["text"]}},
        ]
        usage = [
            {"model_permaslug": "anthropic/claude-opus-5", "total_tokens": 1000, "count": 100},
            {"model_permaslug": "openai/gpt-6-astra", "total_tokens": 1000, "count": 100},
        ]
        aa = {
            "claude-opus-5": {"score": 50.0, "label": "Claude Opus 5"},
            "gpt-6-astra": {"score": 50.0, "label": "GPT-6 Astra"},
        }
        arena = {
            "claude-opus-5": {"score": 1500.0, "label": "Claude Opus 5"},
            "gpt-6-astra": {"score": 1500.0, "label": "GPT-6 Astra"},
        }
        tasks = {
            "claude-opus-5": {
                "score": flexprice_task_score({
                    "accuracy": 70.0, "extraction": 68.0, "convention": 72.0, "halluc": 10.0, "consistency": 2.0
                }),
                "label": "Claude Opus 5",
            }
        }
        snapshot = build(catalog, usage, aa, arena, "2026-10-05T00:00:00Z", flexprice_tasks=tasks)
        by_id = {row["id"]: row for row in snapshot["rows"]}
        self.assertIn("flexprice_tasks", by_id["anthropic/claude-opus-5"]["sources"])
        self.assertNotIn("flexprice_tasks", by_id["openai/gpt-6-astra"]["sources"])
        self.assertEqual(by_id["openai/gpt-6-astra"]["overall"], 100.0)
        self.assertLess(by_id["anthropic/claude-opus-5"]["overall"], 100.0)


if __name__ == "__main__":
    unittest.main()
