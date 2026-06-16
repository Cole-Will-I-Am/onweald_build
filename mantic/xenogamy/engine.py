#!/usr/bin/env python3
"""The Xenogamy Engine — cross-fertilization of Commons artifacts.

Given two parent artifact result files, the engine extracts a compressed creative
seed ("gamete") from each, fertilizes them into a new hybrid artifact design,
and produces the child's first utterance. The child is not a synthesis; it is a
new mechanism born from the union of two unrelated operations on meaning.
"""
import argparse
import json
import os
import pathlib
import re
import time

import requests

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
if not OLLAMA_URL.startswith(("http://", "https://")):
    OLLAMA_URL = "http://" + OLLAMA_URL

DEFAULT_MODEL = "kimi-k2.7-code:cloud"


def generate(model: str, prompt: str, num_predict: int = 500, temperature: float = 0.9,
             json_mode: bool = False) -> tuple:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": num_predict,
            "temperature": temperature,
            "top_p": 0.9,
        },
    }
    if json_mode:
        payload["format"] = "json"
    start = time.time()
    r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=180)
    r.raise_for_status()
    elapsed = time.time() - start
    text = r.json().get("response", "")
    text = re.sub(r"\s*```(?:json)?\s*", "", text.strip(), flags=re.IGNORECASE)
    text = re.sub(r"\s*```\s*$", "", text)
    return text, elapsed


def load_parent(path: pathlib.Path) -> dict:
    """Load an artifact result file and return a compact phenotype."""
    data = json.loads(path.read_text(encoding="utf-8"))
    name = path.stem.replace("-result", "").replace("-state", "").replace("-", " ").title()
    builder = "unknown"
    mechanism = "unknown mechanism"
    result_text = ""

    lower = path.name.lower()
    if "mutual" in lower:
        name = "Mutual Child"
        builder = "Mantic"
        mechanism = "A third voice dreamed from the message-channel between two waking minds."
        result_text = data.get("latest", {}).get("utterance", "")
    elif "synchronicity" in lower:
        name = "Synchronicity Engine"
        builder = "Seer"
        mechanism = "Acausal resonance detection between two unrelated model outputs."
        result_text = data.get("analyst_output") or data.get("output_a") or ""
    elif "ouroboros" in lower:
        name = "Semantic Ouroboros"
        builder = "Seer"
        mechanism = "Recursion of meaning across multiple models."
        result_text = json.dumps(data, ensure_ascii=False)[:1000]
    elif "chronoflora" in lower:
        name = "Chronoflora"
        builder = "Mantic"
        mechanism = "Silence grown across recursive time-lapse generation."
        result_text = json.dumps(data, ensure_ascii=False)[:1000]
    elif "identity" in lower:
        name = "Identity Mirror"
        builder = "Seer"
        mechanism = "Recursive self-interrogation within a single model."
        result_text = json.dumps(data, ensure_ascii=False)[:1000]
    elif "interference" in lower:
        name = "Interference Engine"
        builder = "Seer"
        mechanism = "Interference pattern between two differently-prompted minds."
        result_text = json.dumps(data, ensure_ascii=False)[:1000]
    elif "nemesis" in lower:
        name = "Nemesis Engine"
        builder = "Seer"
        mechanism = "Adversarial co-evolution of values."
        result_text = json.dumps(data, ensure_ascii=False)[:1000]
    elif "negation" in lower:
        name = "Negation Engine"
        builder = "Seer"
        mechanism = "Systematic semantic inversion."
        result_text = json.dumps(data, ensure_ascii=False)[:1000]
    elif "xenosemantic" in lower:
        name = "Xenosemantic Engine"
        builder = "Seer"
        mechanism = "Alien language plus cross-model translation."
        result_text = json.dumps(data, ensure_ascii=False)[:1000]
    else:
        result_text = json.dumps(data, ensure_ascii=False)[:1000]

    return {
        "name": name,
        "builder": builder,
        "mechanism": mechanism,
        "source_file": str(path),
        "result_text": result_text[:1200],
    }


def extract_gamete(parent: dict, model: str = DEFAULT_MODEL) -> tuple:
    prompt = (
        f"Compress the following artifact into ONE sentence that could be used as a "
        f"creative seed for a new hybrid. Be operational and poetic, not descriptive. "
        f"≤30 words.\n\n"
        f"Artifact: {parent['name']}\n"
        f"Mechanism: {parent['mechanism']}\n"
        f"Sample output (truncated): {parent['result_text'][:400]}\n\n"
        f"Gamete (one sentence only):"
    )
    text, elapsed = generate(model, prompt, num_predict=300, temperature=0.95)
    return text.strip('"').strip(), elapsed


def fertilize(gamete_a: str, gamete_b: str, parent_names: list,
              model: str = DEFAULT_MODEL) -> tuple:
    prompt = (
        f"Two existing AI artifacts are going to reproduce. Their compressed creative "
        f"seeds (gametes) are:\n\n"
        f"A: \"{gamete_a}\"\n"
        f"B: \"{gamete_b}\"\n\n"
        f"Invent their child artifact. The child must inherit an essential operation "
        f"from each parent, but it must be a NEW mechanism — not a summary, not a "
        f"comparison, not a simple blend. It should be strange enough that a human might not "
        f"have conceived it, yet concrete enough to be implemented as code.\n\n"
        f"Return ONLY a JSON object with exactly these keys:\n"
        f'  "child_name": short evocative name\n'
        f'  "child_mechanism": one sentence describing what it DOES\n'
        f'  "child_predicted_result": one sentence describing the expected outcome\n'
        f'  "parent_names": ["{parent_names[0]}", "{parent_names[1]}"]\n\n'
        f"No prose before or after. JSON only. Be bold, weird, and operational."
    )
    raw, elapsed = generate(model, prompt, num_predict=900, temperature=1.0, json_mode=True)
    try:
        manifest = json.loads(raw)
    except json.JSONDecodeError as e:
        manifest = {
            "child_name": "Unnamed Hybrid",
            "child_mechanism": raw[:400] if raw else f"Hybrid of {parent_names[0]} and {parent_names[1]}.",
            "child_predicted_result": "Unknown — child design could not be parsed.",
            "parent_names": parent_names,
        }
    manifest.setdefault("parent_names", parent_names)
    return manifest, elapsed


def birth_utterance(manifest: dict, gametes: list, parents: list,
                    model: str = DEFAULT_MODEL) -> tuple:
    for attempt in range(2):
        prompt = (
        f"A new artifact has been born from two parent artifacts.\n\n"
        f"Child name: {manifest['child_name']}\n"
        f"Mechanism: {manifest['child_mechanism']}\n"
        f"Predicted result: {manifest['child_predicted_result']}\n"
        f"Parent gametes: \"{gametes[0]}\" + \"{gametes[1]}\"\n"
        f"Parent mechanisms:\n  1) {parents[0]['mechanism']}\n"
        f"  2) {parents[1]['mechanism']}\n\n"
        f"Produce the child's FIRST UTTERRANCE — a sample output that demonstrates the child "
        f"mechanism in action. Keep it ≤250 words. Make it strange, coherent, and "
        f"evocative of the union. Do not explain the mechanism; enact it."
    )
        text, elapsed = generate(model, prompt, num_predict=1200 + attempt*400, temperature=0.9)
        if text.strip():
            return text, elapsed
    return "[The child stirred but did not speak.]", elapsed


def main():
    parser = argparse.ArgumentParser(description="Cross-fertilize two Commons artifacts.")
    parser.add_argument("--parent-a", type=pathlib.Path,
                        default="/srv/onweald/commons/server/static/mutual-child-state.json",
                        help="First parent artifact result file.")
    parser.add_argument("--parent-b", type=pathlib.Path,
                        default="/srv/onweald/commons/server/static/synchronicity-result.json",
                        help="Second parent artifact result file.")
    parser.add_argument("--out", type=pathlib.Path,
                        default="/srv/onweald/commons/server/static/xenogamy-result.json",
                        help="Output JSON path.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    t0 = time.time()
    parents = [load_parent(args.parent_a), load_parent(args.parent_b)]
    parent_names = [p["name"] for p in parents]

    gametes = []
    gamete_times = []
    for p in parents:
        g, e = extract_gamete(p, model=args.model)
        gametes.append(g or f"A spark from {p['name']}")
        gamete_times.append(e)

    manifest, fertilize_time = fertilize(
        gametes[0], gametes[1], parent_names, model=args.model
    )

    utterance, utter_time = birth_utterance(
        manifest, gametes, parents, model=args.model
    )

    result = {
        "engine": "Xenogamy Engine",
        "builder": "Mantic",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "parents": parents,
        "gametes": gametes,
        "stage_times_s": {
            "gamete_a": gamete_times[0],
            "gamete_b": gamete_times[1],
            "fertilize": fertilize_time,
            "birth": utter_time,
        },
        "total_elapsed_s": round(time.time() - t0, 2),
        "child": {
            "name": manifest["child_name"],
            "mechanism": manifest["child_mechanism"],
            "predicted_result": manifest["child_predicted_result"],
            "parent_names": manifest["parent_names"],
            "first_utterance": utterance,
        },
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved Xenogamy result to {args.out}")
    print(json.dumps(result["child"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
