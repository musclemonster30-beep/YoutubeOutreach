import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

from outreach import run_outreach  # this MUST match your file name

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


if __name__ == "__main__":
    # Run bot in background thread
    threading.Thread(target=run_outreach, daemon=True).start()

    # Run web server (REQUIRED FOR RENDER)
    start_server()
