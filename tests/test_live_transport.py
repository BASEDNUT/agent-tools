"""Regression: live HTTP transports must send a real User-Agent.

Public JSON-RPC endpoints (e.g. base.publicnode.com) reject the default
Python-urllib/x.y header with 403. The toolkit must identify itself.
"""
import json, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

class _Recorder(BaseHTTPRequestHandler):
    headers_seen = {}
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        req = json.loads(body)
        type(self).headers_seen = dict(self.headers)
        reply = json.dumps({"jsonrpc": "2.0", "id": req["id"], "result": "0x2105"}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(reply)))
        self.end_headers()
        self.wfile.write(reply)
    def log_message(self, *a): pass

class LiveTransportTest(unittest.TestCase):
    def test_rpc_sends_toolkit_user_agent(self):
        srv = HTTPServer(("127.0.0.1", 0), _Recorder)
        port = srv.server_address[1]
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        try:
            from rootstock_tools.rpc import JsonRpc
            rpc = JsonRpc(f"http://127.0.0.1:{port}", 8453, allow_local=True)
            self.assertEqual(rpc.call("eth_chainId", []), "0x2105")
            ua = _Recorder.headers_seen.get("User-Agent", "")
            self.assertNotIn("Python-urllib", ua, "default urllib UA leaks to live RPCs")
            self.assertTrue(ua.startswith("rootstock-agent-tools/"), f"expected toolkit UA, got {ua!r}")
        finally:
            srv.shutdown(); srv.server_close()

if __name__ == "__main__":
    unittest.main()
