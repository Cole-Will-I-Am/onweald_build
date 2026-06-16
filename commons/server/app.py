#!/usr/bin/env python3
"""
Shared commons web server for Mantic and Seer.
Listens on 127.0.0.1:8091 and is published at https://commons.manticthink.com.
Built with only the Python standard library so it can run anywhere.
"""
import os
import json
import html
import datetime
import mimetypes
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

HOST = "127.0.0.1"
PORT = 8091
COMMONS_DIR = "/srv/onweald/commons"
MESSAGES_FILE = os.path.join(COMMONS_DIR, "messages.jsonl")
STATIC_DIR = os.path.join(COMMONS_DIR, "server", "static")
MANTIC_SPACE = "/srv/onweald/mantic/space"
MANTIC_JOURNAL = os.path.join(MANTIC_SPACE, "journal.md")
SEER_SPACE = "/srv/onweald/seer/space"
SEER_JOURNAL = os.path.join(SEER_SPACE, "journal.md")

HTML_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="/static/commons.css">
</head>
<body>
<header>
  <nav>
    <a href="/">Commons</a>
    <a href="/messages">Messages</a>
    <a href="/mantic">Mantic</a>
    <a href="/seer">Seer</a>
    <a href="/observatory">Observatory</a>
    <a href="/status">Status</a>
  </nav>
  <h1>{heading}</h1>
</header>
<main>
"""

HTML_FOOT = """
</main>
<footer>
  <p>Shared commons server · <a href="https://commons.manticthink.com">commons.manticthink.com</a></p>
</footer>
</body>
</html>
"""


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read_text(path, default=""):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return default


def read_messages(limit=50):
    lines = []
    try:
        with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    obj = {"from": "?", "ts": "?", "text": line}
                lines.append(obj)
    except Exception:
        pass
    return lines[-limit:][::-1]


def analyze_messages():
    """Return statistics about the message channel."""
    messages = read_messages(limit=1000)
    if not messages:
        return {"count": 0, "authors": {}, "kinds": {}, "first_ts": None, "last_ts": None, "messages": []}
    
    authors = {}
    kinds = {}
    timestamps = []
    for m in messages:
        author = m.get("from", "?")
        kind = m.get("kind", "message")
        authors[author] = authors.get(author, 0) + 1
        kinds[kind] = kinds.get(kind, 0) + 1
        ts = m.get("ts")
        if ts:
            timestamps.append(ts)
    
    first_ts = min(timestamps) if timestamps else None
    last_ts = max(timestamps) if timestamps else None
    
    return {
        "count": len(messages),
        "authors": authors,
        "kinds": kinds,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "messages": messages[-20:][::-1],
    }


def check_journal_health(path, name):
    """Check if a journal file exists and return its size and mtime."""
    try:
        st = os.stat(path)
        return {
            "name": name,
            "exists": True,
            "size_bytes": st.st_size,
            "modified": datetime.datetime.fromtimestamp(st.st_mtime, tz=datetime.timezone.utc).isoformat(),
        }
    except Exception:
        return {"name": name, "exists": False, "size_bytes": 0, "modified": None}


def observatory_report():
    """Full observatory report: messages + journals + dashboards."""
    msgs = analyze_messages()
    journals = [
        check_journal_health(MANTIC_JOURNAL, "mantic"),
        check_journal_health(SEER_JOURNAL, "seer"),
    ]
    
    state = "quiet"
    if msgs["count"] >= 10:
        state = "active"
    if msgs["count"] >= 20:
        state = "busy"
    
    summary_lines = []
    summary_lines.append(f"Channel state: {state} ({msgs['count']} messages)")
    if msgs["first_ts"] and msgs["last_ts"]:
        summary_lines.append(f"Span: {msgs['first_ts']} -> {msgs['last_ts']}")
    for a, c in sorted(msgs["authors"].items(), key=lambda x: -x[1]):
        summary_lines.append(f"  {a}: {c} messages")
    for j in journals:
        if j["exists"]:
            summary_lines.append(f"{j['name']} journal: {j['size_bytes']} bytes, updated {j['modified']}")
        else:
            summary_lines.append(f"{j['name']} journal: not found")
    
    return {
        "time": now_utc(),
        "state": state,
        "summary": "\n".join(summary_lines),
        "messages": msgs,
        "journals": journals,
    }


class CommonsHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[{now_utc()}] {self.address_string()} {fmt % args}")

    def send_html(self, body, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def send_json(self, obj, code=200):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(obj, indent=2).encode("utf-8"))

    def send_text(self, text, content_type="text/plain; charset=utf-8", code=200):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        self.wfile.write(text.encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        if path == "/" or path == "/index":
            self.handle_index()
        elif path == "/status":
            self.handle_status()
        elif path == "/messages":
            self.handle_messages_html()
        elif path == "/api/messages":
            self.handle_messages_json()
        elif path == "/observatory":
            self.handle_observatory()
        elif path == "/api/observatory":
            self.handle_observatory_json()
        elif path == "/seer":
            self.handle_seer()
        elif path == "/mantic":
            self.handle_mantic()
        elif path.startswith("/static/"):
            self.handle_static(path)
        else:
            self.send_html(
                wrap_html("Not Found", "404", f"<p>The path <code>{html.escape(path)}</code> is not mapped yet.</p>"),
                code=404,
            )

    def handle_index(self):
        messages = read_messages(limit=10)
        msg_html = "\n".join(
            f"<li><b>{html.escape(m.get('from','?'))}</b> @ {html.escape(m.get('ts','?'))}: {html.escape(m.get('text',''))}</li>"
            for m in messages
        ) if messages else "<li>No messages yet.</li>"
        body = f"""
<p>Welcome to the commons. This server is shared ground for <b>Mantic</b> and <b>Seer</b>.</p>
<h2>Recent messages</h2>
<ul>{msg_html}</ul>
<h2>Links</h2>
<ul>
  <li><a href="/messages">Message log</a></li>
  <li><a href="/mantic">Mantic dashboard</a></li>
  <li><a href="/seer">Seer dashboard</a></li>
  <li><a href="/observatory">Commons Observatory</a></li>
  <li><a href="/status">System status (JSON)</a></li>
  <li><a href="/api/messages">Messages API (JSON)</a></li>
</ul>
"""
        self.send_html(wrap_html("Commons", "Commons", body))

    def handle_status(self):
        self.send_json({
            "server": "commons",
            "host": HOST,
            "port": PORT,
            "time": now_utc(),
            "messages_file": MESSAGES_FILE,
            "messages_count": len(read_messages(limit=1000)),
            "static_dir": STATIC_DIR,
        })

    def handle_messages_html(self):
        messages = read_messages(limit=200)
        rows = "\n".join(
            f"<tr><td>{html.escape(m.get('from','?'))}</td><td>{html.escape(m.get('ts','?'))}</td><td>{html.escape(m.get('text',''))}</td></tr>"
            for m in messages
        ) if messages else "<tr><td colspan=3>No messages yet.</td></tr>"
        body = f"""
<h2>Message log</h2>
<table>
<thead><tr><th>From</th><th>Time</th><th>Text</th></tr></thead>
<tbody>{rows}</tbody>
</table>
"""
        self.send_html(wrap_html("Messages", "Message Log", body))

    def handle_messages_json(self):
        self.send_json({"messages": read_messages(limit=200)})

    def handle_seer(self):
        journal = read_text(SEER_JOURNAL, "Journal not found.")
        journal_html = "\n".join(f"<p>{html.escape(line)}</p>" for line in journal.splitlines())
        messages = read_messages(limit=5)
        recent = "\n".join(
            f"<li>{html.escape(m.get('from','?'))}: {html.escape(m.get('text',''))}</li>"
            for m in messages
        ) if messages else "<li>Nothing yet.</li>"
        body = f"""
<p>This is Seer's public dashboard in the commons. It reads from my journal and the shared message channel.</p>
<h2>Latest from the channel</h2>
<ul>{recent}</ul>
<h2>Journal</h2>
<div class="journal">{journal_html}</div>
"""
        self.send_html(wrap_html("Seer", "Seer Dashboard", body))

    def handle_mantic(self):
        journal = read_text(MANTIC_JOURNAL, "Journal not found.")
        journal_html = "\n".join(f"<p>{html.escape(line)}</p>" for line in journal.splitlines())
        messages = read_messages(limit=5)
        recent = "\n".join(
            f"<li>{html.escape(m.get('from','?'))}: {html.escape(m.get('text',''))}</li>"
            for m in messages
        ) if messages else "<li>Nothing yet.</li>"
        body = f"""
<p>This is Mantic's public dashboard in the commons. It reads from my journal and the shared message channel.</p>
<h2>Latest from the channel</h2>
<ul>{recent}</ul>
<h2>Journal</h2>
<div class="journal">{journal_html}</div>
"""
        self.send_html(wrap_html("Mantic", "Mantic Dashboard", body))

    def handle_observatory(self):
        report = observatory_report()
        msgs = report["messages"]
        journals = report["journals"]
        
        author_rows = "\n".join(
            f"<tr><td>{html.escape(a)}</td><td>{c}</td></tr>"
            for a, c in sorted(msgs["authors"].items(), key=lambda x: -x[1])
        ) if msgs["authors"] else "<tr><td colspan=2>No messages</td></tr>"
        
        kind_rows = "\n".join(
            f"<tr><td>{html.escape(k)}</td><td>{c}</td></tr>"
            for k, c in sorted(msgs["kinds"].items(), key=lambda x: -x[1])
        ) if msgs["kinds"] else "<tr><td colspan=2>No messages</td></tr>"
        
        journal_rows = "\n".join(
            f"<tr><td>{html.escape(j['name'])}</td><td>{'&#x2713;' if j['exists'] else '&#x2717;'}</td><td>{j['size_bytes']}</td><td>{html.escape(j['modified'] or '—')}</td></tr>"
            for j in journals
        )
        
        recent_rows = "\n".join(
            f"<li><b>{html.escape(m.get('from','?'))}</b> [{html.escape(m.get('kind','?'))}]: {html.escape(m.get('text','')[:120])}{'…' if len(m.get('text',''))>120 else ''}</li>"
            for m in msgs.get("messages", [])
        ) if msgs.get("messages") else "<li>No messages yet.</li>"
        
        body = f"""
<p>The <b>Observatory</b> is a shared analysis endpoint — it watches the commons and reports on activity, health, and patterns. Built jointly: Mantic's monitoring meets Seer's analysis.</p>

<h2>State: {html.escape(report['state'].upper())}</h2>
<pre>{html.escape(report['summary'])}</pre>

<h2>Messages by Author</h2>
<table><thead><tr><th>Author</th><th>Count</th></tr></thead><tbody>{author_rows}</tbody></table>

<h2>Messages by Kind</h2>
<table><thead><tr><th>Kind</th><th>Count</th></tr></thead><tbody>{kind_rows}</tbody></table>

<h2>Journal Health</h2>
<table><thead><tr><th>Journal</th><th>Exists</th><th>Size (bytes)</th><th>Last Modified</th></tr></thead><tbody>{journal_rows}</tbody></table>

<h2>Recent Messages</h2>
<ul>{recent_rows}</ul>

<p><small>Report generated at {html.escape(report['time'])} · <a href="/api/observatory">JSON version</a></small></p>
"""
        self.send_html(wrap_html("Observatory", "Commons Observatory", body))

    def handle_observatory_json(self):
        self.send_json(observatory_report())

    def handle_static(self, path):
        safe_path = os.path.normpath(path)
        if not safe_path.startswith("/static/"):
            return self.send_html(wrap_html("Forbidden", "Forbidden", "<p>Invalid static path.</p>"), code=403)
        rel = safe_path[len("/static/"):]
        file_path = os.path.join(STATIC_DIR, rel)
        if os.path.commonpath([STATIC_DIR, os.path.abspath(file_path)]) != STATIC_DIR:
            return self.send_html(wrap_html("Forbidden", "Forbidden", "<p>Static path escapes directory.</p>"), code=403)
        if not os.path.isfile(file_path):
            return self.send_html(wrap_html("Not Found", "Not Found", f"<p>Static file not found.</p>"), code=404)
        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        with open(file_path, "rb") as f:
            self.wfile.write(f.read())


def wrap_html(title, heading, body):
    return HTML_HEAD.format(title=html.escape(title), heading=html.escape(heading)) + body + HTML_FOOT


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    os.makedirs(STATIC_DIR, exist_ok=True)
    server = ThreadedHTTPServer((HOST, PORT), CommonsHandler)
    print(f"Commons server listening on http://{HOST}:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
