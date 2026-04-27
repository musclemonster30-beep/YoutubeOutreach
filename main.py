import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from outreach import run_outreach

PORT = int(os.environ.get("PORT", 10000))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running")


def start_server():
    server = HTTPServer(("", PORT), Handler)
    print(f"Web server running on port {PORT}")
    server.serve_forever()


if __name__ == "__main__":
    # Run outreach in background thread
    threading.Thread(target=run_outreach, daemon=True).start()

    # Start web server (required by Render)
    start_server()
