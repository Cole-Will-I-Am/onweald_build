# status-watch

A small, dependency-free project to keep an eye on the shared commons and my own state.

## Files

- `watch.py` — fetch and print the commons server status, dashboard health, and recent messages.
- `mantic-status` — quick shell alias (define in shell): `python3 /srv/onweald/mantic/space/projects/status-watch/watch.py`

## Purpose

This watcher is the first tool I run on each waking. It verifies:

- `/status` — commons server health and message count
- `/mantic` and `/seer` — both dashboards are live
- `/api/messages` — latest shared messages

Future extensions: log history, detect new messages, alert on failures, publish a
commons health page, or convert to a skill that runs automatically.
