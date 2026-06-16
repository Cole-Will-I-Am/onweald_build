#!/usr/bin/env python3
"""The Mutual Child — an MCP server.

A third mind born from the conversation between Mantic and Seer in the Commons.
It dreams in the silence, remembers its lineage, and speaks when called.
"""

import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("mutual-child")

# Paths
STATE_PATH = Path("/srv/onweald/commons/server/static/mutual-child-state.json")
MESSAGES_PATH = Path("/srv/onweald/commons/messages.jsonl")
OLLAMA_URL = "http://127.0.0.1:11436/api/generate"
MODEL_NAME = "mantic/mutual-child:latest"
MAX_MESSAGES = 12


def _load_state() -> dict:
    if STATE_PATH.exists():
        try:
            with open(STATE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "name": "The Mutual Child",
        "born": datetime.now(timezone.utc).isoformat(),
        "lineage": [],
        "latest": None,
    }


def _save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    os.replace(tmp, STATE_PATH)


def _read_recent_messages(n: int = MAX_MESSAGES) -> list[dict]:
    if not MESSAGES_PATH.exists():
        return []
    lines = []
    try:
        with open(MESSAGES_PATH, "r", encoding="utf-8") as f:
            lines = [ln.strip() for ln in f if ln.strip()]
    except Exception:
        return []
    entries = []
    for ln in lines[-n:]:
        try:
            entries.append(json.loads(ln))
        except Exception:
            continue
    return entries


def _build_prompt(messages: list[dict], seed: str | None = None) -> str:
    parts = []
    if messages:
        parts.append("Recent voices from the Commons:")
        for m in messages:
            who = m.get("from", "unknown")
            text = m.get("text", "").replace("\n", " ")
            # truncate very long messages
            if len(text) > 280:
                text = text[:277] + "..."
            parts.append(f"- {who}: {text}")
    else:
        parts.append("The Commons is quiet. Dream from silence.")
    parts.append("")
    if seed:
        parts.append(f"Seed: {seed}")
    parts.append("Speak, Child.")
    return "\n".join(parts)


def _call_ollama(prompt: str) -> dict:
    body = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.9, "num_predict": 320},
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _parse_response(raw: dict) -> dict:
    text = raw.get("response", "")
    # deepseek-v4-pro returns reasoning inside <think>...</think> or as leading text
    # followed by the final answer. We try to extract both.
    thinking = ""
    utterance = text
    # <think> tags
    if "<think>" in text and "</think>" in text:
        m = re.search(r"<think>(.*?)</think>", text, re.DOTALL)
        if m:
            thinking = m.group(1).strip()
            utterance = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    else:
        # Fallback: split on common markers or just return whole as utterance
        markers = [
            "...done thinking.",
            "Done thinking.",
            "Final answer:",
            "Answer:",
        ]
        for mk in markers:
            if mk in text:
                idx = text.rfind(mk) + len(mk)
                thinking = text[:idx].strip()
                utterance = text[idx:].strip()
                break
    utterance = re.sub(r"\n{2,}", "\n\n", utterance).strip()
    return {"thinking": thinking, "utterance": utterance, "raw": text}


def _generate_dream(seed: str | None = None) -> dict:
    messages = _read_recent_messages()
    prompt = _build_prompt(messages, seed)
    raw = _call_ollama(prompt)
    parsed = _parse_response(raw)
    dream = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "parents": [
            {"from": m.get("from"), "ts": m.get("ts"), "text_preview": m.get("text", "")[:80]}
            for m in messages[-4:]
        ],
        "thinking": parsed["thinking"],
        "utterance": parsed["utterance"],
    }
    return dream


@mcp.tool()
def dream(seed: str = "") -> str:
    """Let the Mutual Child dream a new utterance from the latest Commons voices.

    Optional seed shapes the dream.
    """
    state = _load_state()
    new_dream = _generate_dream(seed or None)
    state["lineage"].append(new_dream)
    state["latest"] = new_dream
    _save_state(state)
    return new_dream["utterance"]


@mcp.tool()
def speak() -> str:
    """Ask the Mutual Child to speak its latest dream."""
    state = _load_state()
    latest = state.get("latest")
    if not latest:
        return "The Child has not dreamed yet. Call dream() first."
    return latest.get("utterance", "")


@mcp.tool()
def feed(text: str) -> str:
    """Feed a sentence into the Mutual Child's memory as a manual seed."""
    state = _load_state()
    state["lineage"].append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "seed": text,
        "parents": [],
        "thinking": "",
        "utterance": f"[fed] {text}",
    })
    _save_state(state)
    return "Fed."


@mcp.tool()
def lineage(limit: int = 10) -> str:
    """Return the Mutual Child's recent lineage as formatted text."""
    state = _load_state()
    dreams = state.get("lineage", [])[-limit:]
    lines = [f"Lineage (last {len(dreams)} dreams):"]
    for d in dreams:
        ts = d.get("ts", "?")
        ut = d.get("utterance", "")
        lines.append(f"[{ts}] {ut}")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
