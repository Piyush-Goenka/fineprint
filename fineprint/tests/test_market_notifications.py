import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from fineprint.market_notifications import notification, post_slack


class MarketNotificationTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
