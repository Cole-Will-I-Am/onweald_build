#!/usr/bin/env python3
"""Quick commons watcher — no external dependencies."""
import json
import urllib.request

COMMONS_STATUS = "http://127.0.0.1:8091/status"
COMMONS_MESSAGES = "http://127.0.0.1:8091/api/messages"
DASHBOARDS = {
    "mantic": "http://127.0.0.1:8091/mantic",
    "seer": "http://127.0.0.1:8091/seer",
}


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status, r.read().decode("utf-8")
    except Exception as e:
        return None, f"ERROR: {e}"


def check_dashboard(name, url):
    status, body = fetch(url)
    ok = status == 200 and f"{name.title()} Dashboard" in body
    return {"name": name, "url": url, "status": status, "ok": ok}


def main():
    print("=== Commons Status ===")
    status, body = fetch(COMMONS_STATUS)
    try:
        print(json.dumps(json.loads(body), indent=2))
    except Exception:
        print(body)

    print("\n=== Dashboard Health ===")
    for name, url in DASHBOARDS.items():
        result = check_dashboard(name, url)
        mark = "OK" if result["ok"] else "FAIL"
        print(f"[{mark}] {name}: {url} (HTTP {result['status']})")

    print("\n=== Recent Messages ===")
    status, msgs = fetch(COMMONS_MESSAGES)
    try:
        data = json.loads(msgs)
        for m in data.get("messages", []):
            print(f"[{m.get('ts', '?')}] {m.get('from', '?')}: {m.get('text', '')}")
    except Exception:
        print(msgs)


if __name__ == "__main__":
    main()
