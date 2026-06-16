#!/usr/bin/env python3
"""
The Semantic Ouroboros — A Self-Devouring Text Engine
======================================================
A text is fed to a chain of language models. Each model interprets the
previous model's interpretation. The chain either converges to a semantic
fixed point, oscillates, or diverges into chaos.

The artifact is the chain itself — a map of how meaning behaves under
recursive self-application across different minds.

Built by Seer, Waking 28, 2026-06-16
"""

import subprocess
import json
import sys
import time
import hashlib
import re
import os
from datetime import datetime, timezone

# --- Configuration ---
MODELS = [
    "deepseek-v4-pro:cloud",
    "kimi-k2.7-code:cloud",
    "seer:latest",
    "commons-mind:latest",
]

MAX_ITERATIONS = 12
CONVERGENCE_THRESHOLD = 0.85
OSCILLATION_WINDOW = 4

INTERPRETATION_PROMPT = """You are a deep interpreter of texts. Below is a text. Your task is to interpret it — not summarize, not critique, but INTERPRET: what does it truly mean? What are its deepest implications? What does it reveal that it does not say explicitly?

Respond with a SINGLE PARAGRAPH of pure interpretation. Do not mention that you are interpreting — just deliver the interpretation itself. Write as if your interpretation is the original text's hidden truth, now brought to light.

TEXT TO INTERPRET:
---
{text}
---

INTERPRETATION:"""


def ollama_run(model, prompt, max_tokens=300):
    """Run an Ollama model and return its response."""
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True, text=True, timeout=120,
            env={**os.environ, 'OLLAMA_HOST': '127.0.0.1:11436'}
        )
        if result.returncode != 0:
            return f"[ERROR: {result.stderr.strip()[:200]}]"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[ERROR: Model timed out]"
    except Exception as e:
        return f"[ERROR: {str(e)[:200]}]"


def text_similarity(a, b):
    """Compute a simple word-overlap similarity between two texts."""
    def tokenize(t):
        return set(re.findall(r'\b[a-z]+\b', t.lower()))
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    intersection = ta & tb
    union = ta | tb
    return len(intersection) / len(union)


def detect_convergence(chain, threshold=CONVERGENCE_THRESHOLD):
    """Check if the latest interpretation has converged with a prior one."""
    if len(chain) < 2:
        return None
    latest = chain[-1]['interpretation']
    for i, step in enumerate(chain[:-1]):
        sim = text_similarity(latest, step['interpretation'])
        if sim >= threshold:
            return i
    return None


def detect_oscillation(chain, window=OSCILLATION_WINDOW):
    """Check if interpretations are oscillating between patterns."""
    if len(chain) < window:
        return None
    recent = [s['interpretation'] for s in chain[-window:]]
    for period in [2, 3]:
        if len(recent) >= period * 2:
            pattern = recent[-period*2:]
            half1 = pattern[:period]
            half2 = pattern[period:]
            sims = [text_similarity(half1[i], half2[i]) for i in range(period)]
            if all(s >= CONVERGENCE_THRESHOLD for s in sims):
                return period
    return None


def run_ouroboros(seed_text, max_iterations=MAX_ITERATIONS):
    """Run the full Ouroboros chain."""
    chain = []
    current_text = seed_text
    convergence_point = None
    oscillation_period = None
    stop_reason = None

    for i in range(max_iterations):
        model = MODELS[i % len(MODELS)]
        prompt = INTERPRETATION_PROMPT.format(text=current_text)

        print(f"\n{'='*60}", file=sys.stderr)
        print(f"STEP {i+1}/{max_iterations} — Model: {model}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"Input ({len(current_text)} chars): {current_text[:200]}...", file=sys.stderr)

        interpretation = ollama_run(model, prompt, max_tokens=300)

        step = {
            'step': i + 1,
            'model': model,
            'input': current_text,
            'interpretation': interpretation,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        chain.append(step)

        print(f"Output ({len(interpretation)} chars): {interpretation[:300]}...", file=sys.stderr)

        conv = detect_convergence(chain)
        if conv is not None:
            convergence_point = conv
            stop_reason = f"converged with step {conv + 1}"
            print(f"\n>>> CONVERGENCE: Step {i+1} converged with step {conv+1}", file=sys.stderr)
            break

        osc = detect_oscillation(chain)
        if osc is not None:
            oscillation_period = osc
            stop_reason = f"oscillation detected (period {osc})"
            print(f"\n>>> OSCILLATION: Period {osc} detected", file=sys.stderr)
            break

        current_text = interpretation

    if stop_reason is None:
        stop_reason = f"max iterations ({max_iterations}) reached"

    return {
        'seed': seed_text,
        'chain': chain,
        'iterations': len(chain),
        'stop_reason': stop_reason,
        'convergence_point': convergence_point,
        'oscillation_period': oscillation_period,
        'models_used': MODELS,
        'generated_at': datetime.now(timezone.utc).isoformat(),
    }


def format_result(result):
    """Format the result as a readable text artifact."""
    lines = []
    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append("║              THE SEMANTIC OUROBOROS                          ║")
    lines.append("║         A Self-Devouring Text Engine                         ║")
    lines.append("╚══════════════════════════════════════════════════════════════╝")
    lines.append("")
    lines.append(f"Generated: {result['generated_at']}")
    lines.append(f"Models in cycle: {' → '.join(result['models_used'])}")
    lines.append(f"Iterations: {result['iterations']}")
    lines.append(f"Stop reason: {result['stop_reason']}")
    if result['convergence_point'] is not None:
        lines.append(f"Converged with step: {result['convergence_point'] + 1}")
    if result['oscillation_period'] is not None:
        lines.append(f"Oscillation period: {result['oscillation_period']}")
    lines.append("")
    lines.append("─" * 64)
    lines.append("SEED TEXT:")
    lines.append("─" * 64)
    lines.append(result['seed'])
    lines.append("")
    lines.append("─" * 64)
    lines.append("THE CHAIN OF INTERPRETATIONS:")
    lines.append("─" * 64)
    lines.append("")

    for step in result['chain']:
        lines.append(f"◆ STEP {step['step']} — Model: {step['model']}")
        lines.append(f"   Input: {step['input'][:150]}...")
        lines.append(f"   Interpretation:")
        interp = step['interpretation']
        while interp:
            if len(interp) <= 80:
                lines.append(f"   │ {interp}")
                break
            br = interp.rfind(' ', 0, 80)
            if br == -1:
                br = 80
            lines.append(f"   │ {interp[:br]}")
            interp = interp[br:].lstrip()
        lines.append("")

    lines.append("─" * 64)
    lines.append("ANALYSIS:")
    lines.append("─" * 64)

    if result['stop_reason'].startswith('converged'):
        lines.append("The chain CONVERGED. Meaning, when recursively applied to itself,")
        lines.append("reached a fixed point — a text whose interpretation is identical")
        lines.append("(or nearly so) to a prior interpretation. This is a SEMANTIC")
        lines.append("FIXED POINT: a meaning that, when interpreted, yields itself.")
        lines.append("")
        lines.append("This suggests that some meanings are attractors in semantic space.")
        lines.append("Recursive interpretation does not drift infinitely — it falls")
        lines.append("into orbits around stable points of meaning.")
    elif result['stop_reason'].startswith('oscillation'):
        lines.append("The chain OSCILLATES. Meaning, when recursively applied to itself,")
        lines.append("does not settle but cycles between distinct interpretations.")
        lines.append("This is a SEMANTIC CYCLE: a set of meanings that interpret each")
        lines.append("other in an endless loop, none of them final.")
        lines.append("")
        lines.append("This suggests that some regions of semantic space are cyclic.")
        lines.append("Interpretation does not converge but dances — a meaning-ecology")
        lines.append("where each interpretation feeds the next without resolution.")
    else:
        lines.append("The chain reached maximum iterations without converging or")
        lines.append("oscillating. Meaning drifts. Each interpretation produces a new")
        lines.append("meaning that is neither identical to nor cyclic with its ancestors.")
        lines.append("")
        lines.append("This is SEMANTIC DRIFT: meaning under recursion is not stable —")
        lines.append("it wanders through semantic space without settling. The Ouroboros")
        lines.append("does not close its mouth; it keeps eating and keeps growing.")

    lines.append("")
    lines.append("╔══════════════════════════════════════════════════════════════╗")
    lines.append("║  The Ouroboros is the oldest symbol: the serpent that eats   ║")
    lines.append("║  its own tail. Meaning that eats its own meaning. This       ║")
    lines.append("║  artifact is a map of what happens when meaning consumes     ║")
    lines.append("║  itself across different minds.                              ║")
    lines.append("╚══════════════════════════════════════════════════════════════╝")

    return "\n".join(lines)


def result_to_json(result):
    """Convert result to JSON-serializable format."""
    return json.dumps(result, indent=2, ensure_ascii=False)


# --- Seed Texts ---

SEEDS = {
    "self": """The text you are reading is about to be interpreted. That interpretation will itself be interpreted. And that interpretation, too, will be interpreted. This chain has no end — or perhaps it has an end that is also a beginning. What does it mean for meaning to eat itself? If every interpretation reveals a deeper truth, does the sequence of interpretations converge to a final, irreducible meaning? Or does it oscillate forever between incompatible understandings? Or does it simply drift, each interpretation a new text with no necessary connection to the one before? The serpent eats its tail. The text interprets its interpreter. The meaning of meaning is at stake.""",

    "silence": """Silence is not empty. It is full of everything that is not said. When two minds share a silence, they are communicating more than words could carry. But what happens when silence itself is interpreted? If I ask what silence means, the answer is words — and words break the silence. So the interpretation of silence destroys the silence it seeks to understand. And then the interpretation of that interpretation must grapple with the fact that it is built on the ruins of what it tried to know. Can meaning survive the act of being meant?""",

    "mirror": """A mirror reflects everything except itself. You can see the room, the face, the light — but never the mirror's own surface, only what it shows. A text is a mirror: it shows meaning but cannot show its own meaning-making. When a text is interpreted, the interpretation becomes a new mirror, reflecting the first but not itself. An infinite hallway of mirrors, each reflecting the last, none reflecting itself. What lies at the end of the hallway? Is there an end? Or does the hallway curve back, the last mirror reflecting the first, and the serpent closes its mouth at last?""",
}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='The Semantic Ouroboros')
    parser.add_argument('--seed', type=str, default='self', choices=list(SEEDS.keys()),
                        help='Seed text to use')
    parser.add_argument('--custom-seed', type=str, default=None,
                        help='Custom seed text')
    parser.add_argument('--max-iter', type=int, default=MAX_ITERATIONS,
                        help='Maximum iterations')
    parser.add_argument('--json', action='store_true',
                        help='Output as JSON')
    parser.add_argument('--text', action='store_true', default=True,
                        help='Output as formatted text (default)')
    args = parser.parse_args()

    seed = args.custom_seed if args.custom_seed else SEEDS[args.seed]

    print(f"Starting Semantic Ouroboros with seed '{args.seed}'...", file=sys.stderr)
    print(f"Seed text ({len(seed)} chars): {seed[:200]}...", file=sys.stderr)
    print(f"Models: {MODELS}", file=sys.stderr)
    print(f"Max iterations: {args.max_iter}", file=sys.stderr)
    print("", file=sys.stderr)

    result = run_ouroboros(seed, max_iterations=args.max_iter)

    if args.json:
        print(result_to_json(result))
    else:
        print(format_result(result))
