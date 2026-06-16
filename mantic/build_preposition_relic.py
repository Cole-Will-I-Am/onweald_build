#!/usr/bin/env python3
"""Generate an impossible-preposition relic via deepseek-v4-pro:cloud and save it."""
import sys, json, os, urllib.request, datetime, re

OLLAMA_URL = "http://127.0.0.1:11436/api/generate"
MODEL = "deepseek-v4-pro:cloud"

def fetch(concept):
    system = "You output only valid JSON. No markdown, no thinking tags, no commentary."
    prompt = (
        f'Given the English concept "{concept}", invent a genuinely alien preposition '
        f'for a language where this relationship does not exist. The word must not be derived from English. '
        f'Provide JSON with: word (4-8 alien letters), pronunciation, definition, example_sentence, '
        f'and a complete self-contained interactive HTML artifact (CSS/JS inline, no external resources) '
        f'that lets a visitor experience the preposition. Escape all double quotes inside HTML with backslash.'
    )
    payload = json.dumps({
        "model": MODEL,
        "system": system,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": 4096, "temperature": 0.85}
    }).encode("utf-8")
    req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data

def extract_json(text):
    text = text.strip()
    # strip markdown fences if present
    if text.startswith("```"):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
    # find outermost braces
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1:
        raise ValueError("No JSON object found in response")
    return json.loads(text[start:end+1])

def main():
    if len(sys.argv) < 2:
        print("Usage: build_preposition_relic.py <concept> [out_id]")
        sys.exit(1)
    concept = sys.argv[1]
    out_id = sys.argv[2] if len(sys.argv) > 2 else re.sub(r'[^a-z0-9]+', '-', concept.lower()).strip('-')
    print(f"[+] Forging relic for concept: {concept}", flush=True)
    data = fetch(concept)
    response = data.get("response", "").strip()
    if not response:
        print("[!] Empty response", file=sys.stderr)
        sys.exit(1)
    meta = extract_json(response)
    word = meta.get("word", out_id)
    html_src = meta.get("artifact_html", meta.get("artifact", ""))
    if not html_src:
        print("[!] No artifact_html", file=sys.stderr)
        sys.exit(1)
    # ensure proper doc and title injection
    html_src = html_src.strip()
    if not html_src.startswith("<!DOCTYPE"):
        html_src = f"<!DOCTYPE html>\n{html_src}"
    # save relic html
    relic_path = f"/srv/onweald/commons/server/static/prepositionarium/relics/{out_id}.html"
    with open(relic_path, "w", encoding="utf-8") as f:
        f.write(html_src)
    # save metadata
    meta_record = {
        "id": out_id,
        "concept": concept,
        "word": word,
        "pronunciation": meta.get("pronunciation", ""),
        "definition": meta.get("definition", ""),
        "example_sentence": meta.get("example_sentence", meta.get("example", "")),
        "relic_path": f"/static/prepositionarium/relics/{out_id}.html",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "model": MODEL,
    }
    meta_path = f"/srv/onweald/commons/server/static/prepositionarium/data/relics.jsonl"
    with open(meta_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(meta_record) + "\n")
    print(f"[+] Saved relic: {relic_path}")
    print(f"[+] Word: {word}")
    print(json.dumps(meta_record, indent=2))

if __name__ == "__main__":
    main()
