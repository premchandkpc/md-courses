#!/usr/bin/env python3
"""Simple backend server for Engineering Knowledge Universe"""

import json
import mimetypes
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = ROOT / "content"
HTML_FILE = ROOT / "packages" / "legacy-viewer" / "read.html"

def build_tree(directory, prefix=""):
    """Build directory tree structure"""
    items = []
    try:
        for item in sorted(directory.iterdir()):
            if item.name.startswith('.'):
                continue

            if item.is_dir():
                rel_path = prefix + "/" + item.name if prefix else item.name
                items.append({
                    "type": "dir",
                    "name": item.name,
                    "path": rel_path,
                    "children": build_tree(item, rel_path)
                })
            elif item.suffix == ".md":
                rel_path = prefix + "/" + item.name if prefix else item.name
                items.append({
                    "type": "file",
                    "name": item.name,
                    "path": rel_path
                })
    except PermissionError:
        pass

    return items

class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # Tree endpoint
        if path == "/api/tree":
            tree = build_tree(DATA_DIR)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"tree": tree}).encode())

        # File endpoint
        elif path == "/api/file":
            file_path = query.get("path", [""])[0]
            if not file_path:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "path required"}).encode())
                return

            file_path = unquote(file_path)
            full_path = DATA_DIR / file_path

            # Security: prevent directory traversal
            try:
                full_path = full_path.resolve()
                if not str(full_path).startswith(str(DATA_DIR.resolve())):
                    raise ValueError("Path outside data dir")
            except:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid path"}).encode())
                return

            if not full_path.exists() or not full_path.is_file():
                self.send_response(404)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "File not found"}).encode())
                return

            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps({"content": content}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

        # Try to serve actual files from data dir first
        else:
            requested_file = unquote(path.lstrip('/'))
            actual_file = DATA_DIR / requested_file

            # Check if it's a real HTML/other file in data dir
            try:
                actual_file = actual_file.resolve()
                if actual_file.exists() and str(actual_file).startswith(str(DATA_DIR.resolve())):
                    mime_type, _ = mimetypes.guess_type(str(actual_file))
                    try:
                        with open(actual_file, 'rb') as f:
                            content = f.read()
                        self.send_response(200)
                        self.send_header("Content-type", mime_type or "application/octet-stream")
                        self.end_headers()
                        self.wfile.write(content)
                        return
                    except Exception as e:
                        self.send_response(500)
                        self.send_header("Content-type", "text/plain")
                        self.end_headers()
                        self.wfile.write(f"Error: {str(e)}".encode())
                        return
            except:
                pass

            # Fall back to read.html
            if not HTML_FILE.exists():
                self.send_response(404)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(b"read.html not found")
                return

            try:
                with open(HTML_FILE, 'rb') as f:
                    content = f.read()

                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "text/plain")
                self.end_headers()
                self.wfile.write(f"Error: {str(e)}".encode())

    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

if __name__ == "__main__":
    server = HTTPServer(("localhost", 3000), APIHandler)
    print("🚀 Server running on http://localhost:3000")
    print("📚 API endpoints:")
    print("   GET /api/tree     - Get directory structure")
    print("   GET /api/file     - Get file content (path query param)")
    print("   GET /*            - Serve read.html")
    server.serve_forever()
