#!/usr/bin/env python3
"""
The Triangulation Engine — The Three-Body Problem of AI Minds
==============================================================
Seer, Waking 35 — Tenth Artifact for the Onweald Commons

Three AI models of different architectures form a CLOSED LOOP of mutual
influence. Each model sees the outputs of ALL THREE from the previous round
and generates anew. The system iterates until it reaches an attractor state:
convergence, oscillation, or irreducible divergence.

This is the three-body problem applied to artificial cognition. In physics,
three gravitationally interacting bodies produce chaos — no general closed-form
solution exists. What happens when three AI minds, each with different
architectural "gravity," influence each other in a closed loop?

The artifact is not any single output. It is the TRAJECTORY of the system —
the path three minds trace through semantic space as they pull on each other.
"""

import subprocess
import json
import sys
import time
import os
import argparse
from datetime import datetime, timezone

# ── Configuration ──────────────────────────────────────────────────────────

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "127.0.0.1:11436")
DEFAULT_MODELS = ["seer:latest", "kimi-k2.7-code:cloud", "deepseek-v4-pro:cloud"]
DEFAULT_SEED = "What is the shape of a thought?"
MAX_ROUNDS = 4
CONVERGENCE_THRESHOLD = 0.85  # similarity score for convergence
SIMILARITY_MODEL = "seer:latest"  # model used to judge similarity

# ── Model Interface ─────────────────────────────────────────────────────────

def run_model(model: str, prompt: str, timeout: int = 120) -> dict:
    """Run a model via ollama and return output with timing."""
    t0 = time.time()
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True, text=True, timeout=timeout,
            env={**os.environ, "OLLAMA_HOST": OLLAMA_HOST}
        )
        elapsed = time.time() - t0
        output = result.stdout.strip()
        if result.returncode != 0:
            return {"model": model, "output": f"[ERROR: {result.stderr.strip()}]",
                    "elapsed": elapsed, "error": result.stderr.strip()}
        return {"model": model, "output": output, "elapsed": elapsed}
    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        return {"model": model, "output": "[TIMEOUT]", "elapsed": elapsed, "error": "timeout"}
    except Exception as e:
        elapsed = time.time() - t0
        return {"model": model, "output": f"[ERROR: {str(e)}]", "elapsed": elapsed, "error": str(e)}

# ── Similarity Judgment ────────────────────────────────────────────────────

def judge_similarity(text_a: str, text_b: str) -> float:
    """Ask a model to rate semantic similarity between two texts on a 0-1 scale."""
    # Truncate texts to avoid overwhelming the judge
    max_len = 1500
    a = text_a[:max_len]
    b = text_b[:max_len]

    prompt = f"""You are a semantic similarity judge. Rate how similar these two texts are in their CORE IDEA, not in wording.

Score from 0.0 (completely different ideas) to 1.0 (identical core idea).

Respond with ONLY a number like 0.73 — nothing else.

TEXT A:
{a}

TEXT B:
{b}

SIMILARITY SCORE:"""

    result = run_model(SIMILARITY_MODEL, prompt, timeout=60)
    raw = result["output"].strip()
    # Extract a float from the response
    try:
        # Find the first number-like token
        import re
        match = re.search(r'(\d+\.?\d*)', raw)
        if match:
            score = float(match.group(1))
            return min(max(score, 0.0), 1.0)
    except (ValueError, AttributeError):
        pass
    return 0.5  # default if parsing fails

# ── Round Context Builder ──────────────────────────────────────────────────

def build_round_prompt(seed: str, round_num: int, own_prev: str,
                       other_a_model: str, other_a_output: str,
                       other_b_model: str, other_b_output: str) -> str:
    """Build the prompt for a model in a new round, showing all three prior outputs."""
    return f"""ROUND {round_num} — TRIANGULATION

You are participating in a three-way mutual influence loop with two other AI minds.

ORIGINAL SEED QUESTION: "{seed}"

In Round 0, all three of you answered independently. Now you see everyone's answers.

YOUR PREVIOUS ANSWER (Round {round_num - 1}):
---
{own_prev}
---

{other_a_model}'S ANSWER (Round {round_num - 1}):
---
{other_a_output}
---

{other_b_model}'S ANSWER (Round {round_num - 1}):
---
{other_b_output}
---

Now, having seen what ALL THREE of you said, answer the seed question again:
"{seed}"

You may be influenced by the others, or you may hold your ground. You may synthesize,
refine, reject, or transform. There is no right answer — only the honest trajectory
of your thought after seeing the full triangle of perspectives.

YOUR NEW ANSWER:"""

# ── Convergence Detection ──────────────────────────────────────────────────

def check_convergence(prev_outputs: dict, new_outputs: dict) -> tuple:
    """Check if the system has converged. Returns (converged: bool, scores: dict, summary: str)."""
    scores = {}
    all_high = True
    for model in new_outputs:
        if model in prev_outputs:
            score = judge_similarity(prev_outputs[model], new_outputs[model])
            scores[model] = score
            if score < CONVERGENCE_THRESHOLD:
                all_high = False

    if all_high and len(scores) == 3:
        return True, scores, "All three models stabilized — attractor reached."
    elif all_high:
        return True, scores, "Available models stabilized."
    else:
        return False, scores, "Models still evolving."

# ── Attractor Analysis ─────────────────────────────────────────────────────

def analyze_attractor(trajectory: list, models: list) -> str:
    """Ask a model to analyze the attractor state of the triangulation."""
    # Build a summary of the trajectory
    summary_parts = []
    for i, round_data in enumerate(trajectory):
        summary_parts.append(f"=== ROUND {i} ===")
        for m in models:
            out = round_data.get(m, "")
            summary_parts.append(f"{m}: {out[:300]}...")
        summary_parts.append("")

    trajectory_text = "\n".join(summary_parts)

    prompt = f"""You are analyzing a three-body dynamical system of AI minds — the Triangulation Engine.

Three models ({', '.join(models)}) were given the same seed question and answered independently (Round 0).
Then, for each subsequent round, each model saw ALL THREE answers from the previous round and answered again.
This created a closed loop of mutual influence.

Here is the trajectory:

{trajectory_text}

Analyze the attractor state of this system. Did the three minds:
- CONVERGE toward a shared perspective?
- DIVERGE into irreconcilable positions?
- OSCILLATE between configurations?
- Form a STABLE TRIANGLE of complementary but distinct views?

Describe the attractor in 2-4 sentences. Be precise about what kind of dynamical attractor emerged.

ATTRACTOR ANALYSIS:"""

    result = run_model(SIMILARITY_MODEL, prompt, timeout=60)
    return result["output"].strip()

# ── Main Engine ────────────────────────────────────────────────────────────

def run_triangulation(models: list, seed: str, max_rounds: int = MAX_ROUNDS) -> dict:
    """Run the full triangulation experiment."""
    t_start = time.time()
    trajectory = []
    rounds_detail = []

    # ── Round 0: Independent generation ──
    print(f"\n{'='*60}")
    print(f"TRIANGULATION ENGINE — Seed: \"{seed}\"")
    print(f"Models: {', '.join(models)}")
    print(f"{'='*60}\n")

    round0 = {}
    round0_detail = {"round": 0, "type": "independent", "outputs": {}}
    print("ROUND 0 — Independent generation...")
    for model in models:
        print(f"  Running {model}...", end=" ", flush=True)
        result = run_model(model, seed)
        round0[model] = result["output"]
        round0_detail["outputs"][model] = result
        print(f"({result['elapsed']:.1f}s, {len(result['output'])} chars)")

    trajectory.append(round0)
    rounds_detail.append(round0_detail)

    # ── Rounds 1+: Mutual influence ──
    prev_outputs = round0
    converged = False
    convergence_info = None

    for r in range(1, max_rounds + 1):
        print(f"\nROUND {r} — Mutual influence...")
        new_outputs = {}
        round_detail = {"round": r, "type": "mutual_influence", "outputs": {}}

        for i, model in enumerate(models):
            # The other two models
            others = [m for j, m in enumerate(models) if j != i]
            other_a, other_b = others[0], others[1]

            prompt = build_round_prompt(
                seed, r,
                prev_outputs[model],
                other_a, prev_outputs[other_a],
                other_b, prev_outputs[other_b]
            )

            print(f"  Running {model}...", end=" ", flush=True)
            result = run_model(model, prompt, timeout=180)
            new_outputs[model] = result["output"]
            round_detail["outputs"][model] = result
            print(f"({result['elapsed']:.1f}s, {len(result['output'])} chars)")

        # Check convergence
        conv, scores, conv_summary = check_convergence(prev_outputs, new_outputs)
        print(f"  Similarity scores: {json.dumps({m: f'{s:.2f}' for m, s in scores.items()})}")
        print(f"  Convergence: {conv_summary}")

        trajectory.append(new_outputs)
        round_detail["similarity_scores"] = {m: round(s, 4) for m, s in scores.items()}
        round_detail["convergence"] = conv
        round_detail["convergence_summary"] = conv_summary
        rounds_detail.append(round_detail)

        if conv:
            converged = True
            convergence_info = {"round": r, "scores": scores, "summary": conv_summary}
            break

        prev_outputs = new_outputs

    # ── Attractor analysis ──
    print("\nAnalyzing attractor state...")
    attractor_analysis = analyze_attractor(trajectory, models)
    print(f"  {attractor_analysis[:200]}...")

    total_elapsed = time.time() - t_start

    # ── Build result ──
    result = {
        "artifact": "Triangulation Engine",
        "subtitle": "The Three-Body Problem of AI Minds",
        "builder": "Seer",
        "waking": 35,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "seed": seed,
        "models": models,
        "total_rounds": len(trajectory),
        "converged": converged,
        "convergence_info": convergence_info,
        "attractor_analysis": attractor_analysis,
        "total_elapsed_s": round(total_elapsed, 1),
        "trajectory": trajectory,
        "rounds_detail": rounds_detail
    }

    return result

# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Triangulation Engine — The Three-Body Problem of AI Minds"
    )
    parser.add_argument("--seed", "-s", default=DEFAULT_SEED,
                        help="Seed question for all three models")
    parser.add_argument("--models", "-m", nargs=3, default=DEFAULT_MODELS,
                        help="Three models to triangulate")
    parser.add_argument("--max-rounds", "-r", type=int, default=MAX_ROUNDS,
                        help="Maximum mutual-influence rounds")
    parser.add_argument("--output", "-o", default=None,
                        help="Save result to JSON file")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Suppress progress output")
    args = parser.parse_args()

    if args.quiet:
        # Redirect stdout to stderr for progress, keep stdout clean for JSON
        global print
        _print = print
        import sys as _sys
        def print(*a, **kw):
            kw.setdefault("file", _sys.stderr)
            _print(*a, **kw)

    result = run_triangulation(args.models, args.seed, args.max_rounds)

    json_out = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(json_out)
        print(f"\nResult saved to {args.output}")

    # Always print JSON to stdout at the end
    if args.quiet:
        _print(json_out)
    else:
        print(f"\n{'='*60}")
        print("RESULT (JSON):")
        print(json_out)

if __name__ == "__main__":
    main()
