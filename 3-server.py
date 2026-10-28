#!/usr/bin/env python3
"""Local-only BountyHunter preview server, with cautious page-title extraction."""
import json
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, parse_qs
from urllib.request import Request, urlopen


class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/title":
            self.title_response(parse_qs(parsed.query).get("url", [""])[0])
            return
        return super().do_GET()

    def title_response(self, url):
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            self.send_json(400, {"error": "Please provide a valid http(s) URL."})
            return
        try:
            req = Request(url, headers={"User-Agent": "BountyHunter/1.0 (user-requested title extraction)"})
            with urlopen(req, timeout=8) as response:
                text = response.read(500_000).decode("utf-8", "replace")
            match = re.search(r"<title[^>]*>(.*?)</title\s*>", text, re.I | re.S)
            title = re.sub(r"\\s+", " ", re.sub(r"<[^>]+>", "", match.group(1))).strip() if match else ""
            self.send_json(200, {"title": title, "note": "Title extraction only; not eligibility verification."})
        except (URLError, HTTPError, TimeoutError, OSError, ValueError) as exc:
            self.send_json(502, {"error": f"Source could not be read: {exc}"})

    def send_json(self, status, data):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print("[bountyhunter] " + fmt % args)


if __name__ == "__main__":
    print("BountyHunter listening on http://127.0.0.1:8765 (localhost only)")
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
