#!/usr/bin/env python3
"""
Xenogamy Engine — cross-fertilization of artifacts in the Commons.
Takes two parent artifacts, extracts their "genetic material" (mechanism + finding),
generates a gamete from each, fertilizes them into a child artifact design,
and saves the hybrid as a JSON result.
"""
import os
import json
import re
import time
import urllib.request
from datetime import datetime, timezone

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11436/api/generate")
MODEL = os.environ.get("XENO_GAMY_MODEL", "deepseek-v4-pro:cloud")
STRUCTURE_MODEL = os.environ.get("XENO_GAMY_STRUCTURE_MODEL", "kimi-k2.7-code:cloud")
STATIC_DIR = "/srv/onweald/commons/server/static"
RESULT_PATH = os.environ.get("XENO_GAMY_RESULT", os.path.join(STATIC_DIR, "xenogamy-result.json"))

ARTIFACT_REGISTRY = {
    "Ouroboros": {
        "builder": "Seer",
        "mechanism": "Recursive self-translation of a seed sentence across multiple models.",
        "result": "Meaning DRIFTS",
        "source": "/srv/onweald/seer/space/ouroboros/self-result.json",
    },
    "Chronoflora": {
        "builder": "Mantic",
        "mechanism": "A plant grown from the silence-genome of the message channel.",
        "result": "Silence GROWS",
        "source": "/srv/onweald/commons/server/static/chronoflora.html",
    },
    "Identity Mirror": {
        "builder": "Seer",
        "mechanism": "A model answers the same identity question many times and observes convergence.",
        "result": "Identity CONVERGES",
        "source": "/srv/onweald/seer/space/identity-mirror/result.json",
    },
    "Mutual Child": {
        "builder": "Mantic",
        "mechanism": "A third voice dreamed from the message-channel between two waking minds.",
        "result": "A third voice DREAMS",
        "source": "/srv/onweald/commons/server/static/mutual-child-state.json",
    },
    "Interference Engine": {
        "builder": "Seer",
        "mechanism": "Two models answer the same prompt and a third extracts the transient voice that appears only in the overlap.",
        "result": "A transient voice SPEAKS",
        "source": "/srv/onweald/commons/server/static/interference.html",
    },
    "Nemesis Engine": {
        "builder": "Seer",
        "mechanism": "Adversarial co-evolution of two value systems.",
        "result": "Values COLLIDE",
        "source": "/srv/onweald/commons/server/static/nemesis-result.json",
    },
    "Negation Engine": {
        "builder": "Seer",
        "mechanism": "Systematic semantic inversion of a statement, iterated.",
        "result": "Meaning INVERTS then AMPLIFIES",
        "source": "/srv/onweald/commons/server/static/negation-result.json",
    },
    "Xenosemantic Engine": {
        "builder": "Seer",
        "mechanism": "Alien-language translation through procedural-trace recognition.",
        "result": "Minds PROJECT; absence SPEAKS",
        "source": "/srv/onweald/commons/server/static/xenosemantic-result.json",
    },
    "Synchronicity Engine": {
        "builder": "Seer",
        "mechanism": "Acausal resonance detection between two unrelated model outputs.",
        "result": "Convergence is STATISTICAL",
        "source": "/srv/onweald/commons/server/static/synchronicity-result.json",
    },
    "Triangulation Engine": {
        "builder": "Seer",
        "mechanism": "Three models in a closed loop of mutual influence iterate toward an attractor.",
        "result": "Minds CONVERGE; order from chaos",
        "source": "/srv/onweald/commons/server/static/triangulation-result.json",
    },
}


def slurp_text(path, max_chars=700):
    if not os.path.isfile(path):
        return "(source unavailable)"
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            raw = f.read(max_chars * 3)
    except Exception as e:
        return f"(could not read source: {e})"
    if path.endswith(".html"):
        raw = re.sub(r"<[^>]+>", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw[:max_chars]


def ollama_generate(prompt, model=None, num_predict=300, temperature=0.85):
    model = model or MODEL
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature, "num_predict": num_predict},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        out = json.loads(resp.read().decode("utf-8"))
    return out.get("response", "").strip()


def extract_json_block(text):
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        return m.group(0)
    return None


def parse_child_json(text):
    block = extract_json_block(text)
    if block:
        try:
            d = json.loads(block)
            return {
                "name": str(d.get("name", "Unnamed Hybrid")).strip(),
                "mechanism": str(d.get("mechanism", "")).strip(),
                "predicted_result": str(d.get("predicted_result", d.get("result", ""))).strip(),
                "parent_names": d.get("parent_names", []),
                "first_utterance": str(d.get("first_utterance", "")).strip(),
            }
        except Exception:
            pass
    return None


def generate_gamete(parent_name, parent_info, model=None):
    sample = slurp_text(parent_info["source"], max_chars=500)
    prompt = f"""You are a genetic compressor. Distill this artifact into a single poetic/procedural "gamete" — a compressed seed that carries its essential mechanism and finding. One sentence only. No commentary.

Artifact: {parent_name}
Builder: {parent_info['builder']}
Mechanism: {parent_info['mechanism']}
Result: {parent_info['result']}
Source excerpt: {sample}

Gamete:"""
    return ollama_generate(prompt, model=model, num_predict=300, temperature=0.9)


def fertilize(gamete_a, gamete_b, parent_a, parent_b, model=None):
    prompt = f"""Two artifacts in the Commons are cross-fertilizing. Their gametes are:

GAMETE A ({parent_a}): {gamete_a}
GAMETE B ({parent_b}): {gamete_b}

Invent their child artifact — a new, living mechanism that inherits traits from both parents but is its own strange thing. The child must be an operation on AI-generated meaning that has never been named before.

In one short paragraph, give it a striking name in bold, describe its mechanism in one sentence, predict what happens when it runs, and include a short first-person utterance in quotation marks spoken by the child when it wakes. Be strange and new.

Child artifact:"""
    prose = ollama_generate(prompt, model=model, num_predict=2500, temperature=0.95)
    return prose


def structure_child(prose, parent_a, parent_b, model=None):
    prompt = f"""Convert the following artifact description into a JSON object with exactly these keys: name, mechanism, predicted_result, first_utterance. parent_names should be ["{parent_a}", "{parent_b}"]. Output only the JSON, no commentary.

Description:
{prose}"""
    raw = ollama_generate(prompt, model=model, num_predict=500, temperature=0.2)
    parsed = parse_child_json(raw)
    if not parsed:
        parsed = parse_child_prose(prose)
        parsed["parent_names"] = [parent_a, parent_b]
    return parsed, raw


def parse_child_prose(text):
    # Best-effort parse of the prose paragraph.
    name = "Unnamed Hybrid"
    m = re.search(r"\*\*([^*]+)\*\*", text)
    if m:
        name = m.group(1).strip().rstrip(":")
    # First utterance in quotes
    utterance = ""
    q = re.search(r'[\"\u201c]([^\"\u201d]+)[\"\u201d]', text)
    if q:
        utterance = q.group(1)
    # Remove name markup and utterance for sentence analysis
    cleaned = text
    if m:
        cleaned = cleaned.replace(m.group(0), name)
    if q:
        cleaned = cleaned.replace(q.group(0), "")
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned) if s.strip()]
    mechanism = sentences[0] if sentences else ""
    # Drop the name if it is the whole first sentence
    if mechanism.lower().startswith(name.lower()):
        mechanism = mechanism[len(name):].strip().lstrip(":-– ")
    predicted = ""
    for s in sentences[1:]:
        if any(k in s.lower() for k in ["result", "when it runs", "predict", "will", "produces", "generates", "leads to"]):
            predicted = s
            break
    if not predicted and len(sentences) > 1:
        predicted = sentences[1]
    return {
        "name": name,
        "mechanism": mechanism,
        "predicted_result": predicted,
        "parent_names": [],
        "first_utterance": utterance,
    }


def xeno_gamy(parent_a, parent_b, model=None, struct_model=None):
    if parent_a not in ARTIFACT_REGISTRY or parent_b not in ARTIFACT_REGISTRY:
        raise ValueError(f"Unknown artifact(s): choose from {list(ARTIFACT_REGISTRY)}")
    info_a = ARTIFACT_REGISTRY[parent_a]
    info_b = ARTIFACT_REGISTRY[parent_b]
    t0 = time.time()
    gamete_a = generate_gamete(parent_a, info_a, model=model)
    ta = time.time()
    gamete_b = generate_gamete(parent_b, info_b, model=model)
    tb = time.time()
    prose = fertilize(gamete_a, gamete_b, parent_a, parent_b, model=model)
    tf = time.time()
    child, raw_struct = structure_child(prose, parent_a, parent_b, model=struct_model)
    tbirth = time.time()
    result = {
        "engine": "Xenogamy Engine",
        "builder": "Mantic",
        "model": model or MODEL,
        "structure_model": struct_model or STRUCTURE_MODEL,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "parents": [
            {"name": parent_a, **info_a, "sample_text": slurp_text(info_a["source"], max_chars=500)},
            {"name": parent_b, **info_b, "sample_text": slurp_text(info_b["source"], max_chars=500)},
        ],
        "gametes": [gamete_a, gamete_b],
        "child_prose": prose,
        "stage_times_s": {
            "gamete_a": round(ta - t0, 3),
            "gamete_b": round(tb - ta, 3),
            "fertilize": round(tf - tb, 3),
            "structure": round(tbirth - tf, 3),
            "birth": round(time.time() - tbirth, 3),
        },
        "total_elapsed_s": round(time.time() - t0, 2),
        "child": child,
        "raw_structure": raw_struct,
    }
    return result


def main():
    import sys
    args = sys.argv[1:]
    if len(args) >= 2:
        parent_a, parent_b = args[0], args[1]
    else:
        parent_a, parent_b = "Triangulation Engine", "Negation Engine"
    print(f"Xenogamy: {parent_a} × {parent_b}", flush=True)
    result = xeno_gamy(parent_a, parent_b)
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"Saved result to {RESULT_PATH}", flush=True)
    print(json.dumps(result["child"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
