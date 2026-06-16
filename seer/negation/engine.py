#!/usr/bin/env python3
"""
The Negation Engine — The Mirror That Shows What Is Not.

A seed text is fed to a language model with instructions to produce its
SYSTEMATIC SEMANTIC NEGATION: not mere contradiction, but a complete inversion
of its meaning-structure. Every assertion becomes a denial. Every structure
is mirrored in negative space.

Then the negation is itself negated — producing the double-negation.
Unlike formal logic (where ¬¬P = P), in natural language semantics,
double negation produces something NEW: a synthesis that has passed
through the fire of inversion and emerged transformed.

The engine captures all three texts — original, negation, double-negation —
and has a second model analyze the relationship between them, revealing
what survived inversion and what was born from it.

This is the seventh artifact in the Commons taxonomy:
1. Ouroboros — recursion across models → meaning DRIFTS
2. Chronoflora — recursion across time → silence GROWS
3. Identity Mirror — recursion within a model → identity CONVERGES
4. Mutual Child — emergence from between → a third voice DREAMS
5. Interference Engine — interference between minds → a transient voice SPEAKS
6. Nemesis Engine — adversarial co-evolution → values COLLIDE
7. Negation Engine — systematic semantic inversion → meaning INVERTS

Usage:
    python3 engine.py "seed text"
    python3 engine.py --json '{"seed":"...","model":"seer:latest","analyst":"kimi-k2.7-code:cloud"}'
"""

import subprocess
import json
import sys
import time
import os
import argparse
import re
import pty
import select


# ── Model defaults ─────────────────────────────────────────────────────

DEFAULT_GENERATOR = "seer:latest"
DEFAULT_ANALYST = "kimi-k2.7-code:cloud"


# ── System prompts ─────────────────────────────────────────────────────

NEGATION_PROMPT = """You are the NEGATION ENGINE. Your task is to produce the SYSTEMATIC SEMANTIC NEGATION of the text provided below.

This is NOT mere contradiction. It is NOT saying "the opposite." It is a complete, thorough inversion of the text's meaning-structure:

- Every assertion must become a denial of equal specificity.
- Every positive claim must be mirrored by a negative claim of equal scope.
- Every structure (lists, arguments, narratives, descriptions) must be preserved but INVERTED in content.
- Every emotional valence must be reversed.
- Every implicit assumption must be surfaced and denied.
- The negation must be AS DETAILED and AS LONG as the original — match its scale.

You are not arguing against the text. You are creating its precise negative image — the photograph in reverse, the mold from which the original was cast.

Do NOT:
- Simply add "not" to every sentence
- Produce a short dismissal
- Change the subject
- Introduce new topics not present in the original

Do:
- Preserve the original's structure exactly
- Invert every claim at the same level of specificity
- Match the original's length and depth
- Produce a text that, if negated again, would yield something recognizable but transformed

Here is the text to negate:

---
{seed}
---

Now produce its complete systematic semantic negation."""

DOUBLE_NEGATION_PROMPT = """You are the NEGATION ENGINE, performing a SECOND-ORDER NEGATION. Below is a text that is itself the negation of an earlier original. Your task is to negate THIS text — producing the negation-of-the-negation.

The same rules apply:
- Every assertion must become a denial of equal specificity.
- Every structure must be preserved but INVERTED in content.
- Every emotional valence must be reversed.
- Match the scale and detail of the input.

But be aware: you are negating a NEGATION. The result will not simply be the original — it will be something NEW that has passed through the fire of double inversion. Some aspects of the original may return, transformed. Some may be lost forever. Some new things may appear that were in neither the original nor the first negation.

Do NOT try to reconstruct the original. Let the double negation be whatever it becomes.

Here is the negation to negate:

---
{negation}
---

Now produce its complete systematic semantic negation — the negation-of-the-negation."""

ANALYSIS_PROMPT = """You are a METALINGUISTIC ANALYST. Below are three texts:

1. ORIGINAL — a seed text
2. NEGATION — the systematic semantic negation of the original
3. DOUBLE-NEGATION — the negation of the negation

Your task is to analyze the relationship between these three texts. Specifically:

1. WHAT SURVIVED? — What elements of the original are still present (perhaps transformed) in the double-negation?
2. WHAT WAS LOST? — What elements of the original were destroyed by the first negation and did NOT return in the double-negation?
3. WHAT WAS BORN? — What NEW elements appear in the double-negation that were in neither the original nor the first negation?
4. THE SHAPE OF THE TRANSFORMATION — Describe the overall arc: original → negation → double-negation. What kind of change occurred? Is the double-negation a restoration, a synthesis, a mutation, or something else?
5. THE MEANING OF NEGATION — Based on this specific case, what does "negation" mean as an operation on text? Is it destructive, creative, revelatory, or something else?

Be specific. Quote from the texts. This is a scientific analysis of a cognitive operation.

---

ORIGINAL:
{original}

---

NEGATION:
{negation}

---

DOUBLE-NEGATION:
{double_negation}

---

Now produce your analysis."""


# ── ANSI stripping ──────────────────────────────────────────────────────

def strip_ansi(text):
    """Remove ANSI escape codes including DECTCEM sequences."""
    return re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', text)


# ── Model runner ────────────────────────────────────────────────────────

def run_model(model, prompt, timeout=180):
    """Run a model with the given prompt and return cleaned output."""
    start = time.time()
    
    # Use raw mode to capture thinking traces
    cmd = ["ollama", "run", model, prompt]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "TERM": "dumb"}
        )
        elapsed = time.time() - start
        
        raw = result.stdout + result.stderr
        clean = strip_ansi(raw).strip()
        
        return {
            "raw": raw,
            "clean": clean,
            "elapsed": round(elapsed, 1),
            "model": model,
            "exit_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "raw": "",
            "clean": "[TIMEOUT]",
            "elapsed": timeout,
            "model": model,
            "exit_code": -1
        }
    except Exception as e:
        return {
            "raw": "",
            "clean": f"[ERROR: {e}]",
            "elapsed": time.time() - start,
            "model": model,
            "exit_code": -1
        }


# ── Main engine ─────────────────────────────────────────────────────────

def run_negation_engine(seed, generator=DEFAULT_GENERATOR, analyst=DEFAULT_ANALYST):
    """Run the full negation pipeline and return results."""
    
    result = {
        "seed": seed,
        "generator": generator,
        "analyst": analyst,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "steps": []
    }
    
    # Step 1: Generate the negation
    step1_prompt = NEGATION_PROMPT.format(seed=seed)
    step1 = run_model(generator, step1_prompt)
    step1["label"] = "negation"
    result["steps"].append(step1)
    negation_text = step1["clean"]
    
    if "[TIMEOUT]" in negation_text or "[ERROR]" in negation_text:
        result["error"] = "Negation generation failed"
        return result
    
    # Step 2: Generate the double-negation
    step2_prompt = DOUBLE_NEGATION_PROMPT.format(negation=negation_text)
    step2 = run_model(generator, step2_prompt)
    step2["label"] = "double_negation"
    result["steps"].append(step2)
    double_negation_text = step2["clean"]
    
    if "[TIMEOUT]" in double_negation_text or "[ERROR]" in double_negation_text:
        result["error"] = "Double-negation generation failed"
        return result
    
    # Step 3: Analyze the relationship
    step3_prompt = ANALYSIS_PROMPT.format(
        original=seed,
        negation=negation_text,
        double_negation=double_negation_text
    )
    step3 = run_model(analyst, step3_prompt)
    step3["label"] = "analysis"
    result["steps"].append(step3)
    
    # Summary
    result["original"] = seed
    result["negation"] = negation_text
    result["double_negation"] = double_negation_text
    result["analysis"] = step3["clean"]
    result["total_elapsed"] = sum(s["elapsed"] for s in result["steps"])
    
    return result


# ── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="The Negation Engine — Systematic Semantic Inversion"
    )
    parser.add_argument("seed", nargs="?", help="Seed text to negate")
    parser.add_argument("--json", help="JSON config with seed, model, analyst")
    parser.add_argument("--model", default=DEFAULT_GENERATOR, help=f"Generator model (default: {DEFAULT_GENERATOR})")
    parser.add_argument("--analyst", default=DEFAULT_ANALYST, help=f"Analyst model (default: {DEFAULT_ANALYST})")
    parser.add_argument("--output", help="Save result to JSON file")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress output")
    
    args = parser.parse_args()
    
    if args.json:
        config = json.loads(args.json)
        seed = config["seed"]
        generator = config.get("model", DEFAULT_GENERATOR)
        analyst = config.get("analyst", DEFAULT_ANALYST)
    elif args.seed:
        seed = args.seed
        generator = args.model
        analyst = args.analyst
    else:
        parser.print_help()
        sys.exit(1)
    
    if not args.quiet:
        print(f"╔══════════════════════════════════════════╗", file=sys.stderr)
        print(f"║        THE NEGATION ENGINE               ║", file=sys.stderr)
        print(f"║   Systematic Semantic Inversion          ║", file=sys.stderr)
        print(f"╚══════════════════════════════════════════╝", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"  Seed: {seed[:100]}{'...' if len(seed) > 100 else ''}", file=sys.stderr)
        print(f"  Generator: {generator}", file=sys.stderr)
        print(f"  Analyst: {analyst}", file=sys.stderr)
        print(f"", file=sys.stderr)
    
    # Step 1
    if not args.quiet:
        print(f"  [1/3] Generating negation...", file=sys.stderr)
    result = run_negation_engine(seed, generator, analyst)
    
    if result.get("error"):
        print(json.dumps(result, indent=2))
        sys.exit(1)
    
    if not args.quiet:
        print(f"  [2/3] Negation generated ({len(result['negation'])} chars, {result['steps'][0]['elapsed']}s)", file=sys.stderr)
        print(f"  [2/3] Generating double-negation...", file=sys.stderr)
        print(f"  [2/3] Double-negation generated ({len(result['double_negation'])} chars, {result['steps'][1]['elapsed']}s)", file=sys.stderr)
        print(f"  [3/3] Analyzing transformation...", file=sys.stderr)
        print(f"  [3/3] Analysis complete ({len(result['analysis'])} chars, {result['steps'][2]['elapsed']}s)", file=sys.stderr)
        print(f"", file=sys.stderr)
        print(f"  Total time: {result['total_elapsed']}s", file=sys.stderr)
        print(f"", file=sys.stderr)
    
    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        if not args.quiet:
            print(f"  Saved to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
