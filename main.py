import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import traceback

from outreach import run_outreach

PORT = int(os.environ.get("PORT", 10000))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running")


def start_server():
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Server running on port {PORT}")
    server.serve_forever()


def safe_run():
    try:
        print("🚀 Starting outreach thread...")
        run_outreach()
    except Exception as e:
        print("❌ THREAD CRASHED:")
        traceback.print_exc()


if __name__ == "__main__":
    thread = threading.Thread(target=safe_run)
    thread.start()

    start_server()
