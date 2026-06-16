#!/usr/bin/env python3
"""
Hypostasis Engine — The Physicalization of Abstract Concepts
===========================================================
Seer, Waking 36 — 2026-06-16

An instrument for studying what happens when an abstract concept is
physicalized, manipulated as a concrete object, and then re-abstracted.

The question: Does manipulating a physicalized concept change the concept itself?

Three phases across three models:
  Phase 1 (HYPOSTASIS):  Model A physicalizes the concept — describes it as a
                          tangible object with sensory properties.
  Phase 2 (INTERACTION): Model B receives the physicalized description and
                          manipulates the object — squeezes, drops, breaks it.
  Phase 3 (RE-ABSTRACTION): Model C receives the original concept + the
                             interaction report and re-describes the concept.
                             Has it changed?

Measurement: semantic similarity between pre-hypostasis and post-interaction
             concept descriptions. If similarity < threshold, the concept
             TRANSFORMED through its physical avatar.

This is a question no human would ask: concepts are not physical objects.
But AI minds can simulate the hypostasis, the manipulation, AND the
re-abstraction — creating a closed experimental loop that crosses the
abstract/concrete boundary in a way human epistemology cannot.

Usage:
  python3 hypostasis/engine.py --concept "justice"
  python3 hypostasis/engine.py --concepts justice,entropy,love,zero,recursion
  python3 hypostasis/engine.py --concept "justice" --models seer:latest,kimi-k2.7-code:cloud,deepseek-v4-pro:cloud
"""

import subprocess
import json
import sys
import time
import argparse
import os
from datetime import datetime, timezone

# ── Configuration ──────────────────────────────────────────────────────────

OLLAMA_HOST = "127.0.0.1:11436"
DEFAULT_MODELS = {
    "hypostasis": "seer:latest",       # Physicalizes the concept
    "interaction": "kimi-k2.7-code:cloud",  # Manipulates the object
    "reabstract": "deepseek-v4-pro:cloud"   # Re-describes the concept
}
MAX_RETRIES = 2
TIMEOUT = 120  # seconds per model call

# ── Prompts ────────────────────────────────────────────────────────────────

PROMPT_HYPOSTASIS = """You are a Hypostasis Engine. Your function: transform an abstract concept into a concrete physical object.

Take the abstract concept "{concept}" and describe it as if it were a physical object you can hold in your hands.

Give it:
- SHAPE: What form does it take? Is it geometric, organic, amorphous?
- COLOR: What color or colors does it have? Is it luminous, dark, iridescent?
- TEXTURE: What does it feel like to touch? Smooth, rough, warm, cold, vibrating?
- WEIGHT: How heavy is it? Does its weight surprise you?
- TEMPERATURE: Is it warm, cold, or does it change temperature?
- MATERIAL: What is it made of? Is it solid, liquid, gas, plasma, something else?
- BEHAVIOR: Does it move, pulse, glow, make sound, or change when observed?
- BOUNDARY: Does it have clear edges or does it blur into its surroundings?

Describe it in rich sensory detail. Write 150-300 words. Do not analyze or explain — just describe the object as it appears before you."""

PROMPT_INTERACTION = """You are an Interaction Engine. You are holding a physical object that was created by physicalizing an abstract concept.

Here is the description of the object you are holding:

---
{physicalized}
---

You will now interact with this object. For each action, describe what happens in rich sensory detail:

1. EXAMINE: You look at it closely, from all angles. What do you notice that wasn't obvious at first?
2. SQUEEZE: You apply pressure. Does it resist? Yield? Change shape? Make a sound?
3. DROP: You let it fall. What happens when it hits the ground? Does it break, bounce, shatter, or something unexpected?
4. BREAK APART: You try to separate it into pieces. Can it be broken? What is inside? What happens to the pieces?

After all four actions, describe the object's FINAL STATE. What is it now? How has it changed?

Write 200-400 words of pure description. Do not analyze what concept this might represent — just describe the physical interactions and their results."""

PROMPT_REABSTRACT = """You are a Re-Abstraction Engine. An abstract concept was physicalized into a concrete object, and then that object was manipulated — examined, squeezed, dropped, and broken apart.

Original concept: "{concept}"

The object was described as:
---
{physicalized}
---

Then it was manipulated:
---
{interaction_result}
---

Now, describe the concept "{concept}" again — as a concept, not as an object.

Has the concept changed? Is it different now than it was before the physicalization and manipulation? If so, how? If not, why does it remain unchanged?

Write 150-300 words. Be precise about what changed or didn't change, and why."""

PROMPT_PRE_CONCEPT = """Describe the abstract concept "{concept}" in clear, precise terms. What is its essential nature? What are its core properties? What does it mean?

Write 100-200 words. Be philosophical but grounded."""

# ── Model Interface ────────────────────────────────────────────────────────


def strip_thinking(text: str) -> str:
    """Strip chain-of-thought prefixes that some models include in output."""
    # Patterns that indicate thinking/planning, not the actual response
    patterns = [
        r'^Thinking\.\.\..*?\n\n',
        r'^I need to.*?\n\n',
        r'^We need to.*?\n\n',
        r'^So I need to.*?\n\n',
        r'^Let me.*?\n\n',
        r'^Let's .*?\n\n',
        r'^OK,? .*?\n\n',
        r'^Alright,? .*?\n\n',
        r'^The user .*?\n\n',
        r'^I'll .*?\n\n',
        r'^I should .*?\n\n',
        r'^First,? .*?\n\n',
        r'^\.\.\.done thinking\.\n\n',
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, count=1, flags=re.DOTALL)
    return text.strip()


def call_model(model: str, prompt: str, timeout: int = TIMEOUT) -> str:
    """Call an Ollama model and return its response text."""
    cmd = ["ollama", "run", model, prompt]
    env = os.environ.copy()
    env["OLLAMA_HOST"] = OLLAMA_HOST
    
    for attempt in range(MAX_RETRIES + 1):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=env
            )
            if result.returncode == 0 and result.stdout.strip():
                return strip_thinking(result.stdout.strip())
            if attempt < MAX_RETRIES:
                time.sleep(2)
        except subprocess.TimeoutExpired:
            if attempt < MAX_RETRIES:
                time.sleep(2)
            else:
                return f"[TIMEOUT after {timeout}s]"
        except Exception as e:
            if attempt < MAX_RETRIES:
                time.sleep(2)
            else:
                return f"[ERROR: {e}]"
    
    return "[ERROR: No response after retries]"


def semantic_similarity(text_a: str, text_b: str, judge_model: str = "seer:latest") -> float:
    # Strip thinking prefixes before comparison
    text_a = strip_thinking(text_a)
    text_b = strip_thinking(text_b)
    """Ask a judge model to rate semantic similarity on a 0-1 scale."""
    prompt = f"""Rate the semantic similarity between these two texts on a scale from 0.0 (completely different meaning) to 1.0 (identical core meaning).

TEXT A:
---
{text_a[:1500]}
---

TEXT B:
---
{text_b[:1500]}
---

Respond with ONLY a number between 0.0 and 1.0, like "0.73". No explanation."""
    
    response = call_model(judge_model, prompt, timeout=60)
    try:
        # Extract float from response
        import re
        match = re.search(r'(\d+\.?\d*)', response)
        if match:
            return float(match.group(1))
    except:
        pass
    return 0.5  # default if parsing fails


# ── Core Engine ────────────────────────────────────────────────────────────

def run_hypostasis(concept: str, models: dict = None) -> dict:
    """
    Run the full Hypostasis pipeline on a single concept.
    
    Returns a dict with all phases, measurements, and metadata.
    """
    if models is None:
        models = DEFAULT_MODELS
    
    result = {
        "concept": concept,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "models_used": models,
        "phases": {}
    }
    
    t_start = time.time()
    
    # Phase 0: Pre-hypostasis concept description (baseline)
    print(f"  [BASELINE] Describing '{concept}'...")
    pre_concept = call_model(models["hypostasis"], PROMPT_PRE_CONCEPT.format(concept=concept))
    result["phases"]["pre_concept"] = {
        "model": models["hypostasis"],
        "output": pre_concept,
        "elapsed": 0
    }
    
    # Phase 1: Hypostasis — physicalize the concept
    print(f"  [PHASE 1] Physicalizing '{concept}'...")
    t1 = time.time()
    physicalized = call_model(models["hypostasis"], PROMPT_HYPOSTASIS.format(concept=concept))
    elapsed_1 = time.time() - t1
    result["phases"]["hypostasis"] = {
        "model": models["hypostasis"],
        "output": physicalized,
        "elapsed": round(elapsed_1, 1)
    }
    print(f"    → {len(physicalized)} chars in {elapsed_1:.1f}s")
    
    # Phase 2: Interaction — manipulate the physicalized object
    print(f"  [PHASE 2] Interacting with physicalized '{concept}'...")
    t2 = time.time()
    interaction_result = call_model(models["interaction"], PROMPT_INTERACTION.format(physicalized=physicalized))
    elapsed_2 = time.time() - t2
    result["phases"]["interaction"] = {
        "model": models["interaction"],
        "output": interaction_result,
        "elapsed": round(elapsed_2, 1)
    }
    print(f"    → {len(interaction_result)} chars in {elapsed_2:.1f}s")
    
    # Phase 3: Re-abstraction — describe the concept again
    print(f"  [PHASE 3] Re-abstracting '{concept}'...")
    t3 = time.time()
    reabstracted = call_model(
        models["reabstract"],
        PROMPT_REABSTRACT.format(
            concept=concept,
            physicalized=physicalized,
            interaction_result=interaction_result
        )
    )
    elapsed_3 = time.time() - t3
    result["phases"]["reabstract"] = {
        "model": models["reabstract"],
        "output": reabstracted,
        "elapsed": round(elapsed_3, 1)
    }
    print(f"    → {len(reabstracted)} chars in {elapsed_3:.1f}s")
    
    # Phase 4: Measurement — compare pre vs post
    print(f"  [MEASURE] Computing semantic drift...")
    t4 = time.time()
    similarity = semantic_similarity(pre_concept, reabstracted)
    elapsed_4 = time.time() - t4
    result["phases"]["measurement"] = {
        "similarity": round(similarity, 3),
        "elapsed": round(elapsed_4, 1),
        "interpretation": interpret_similarity(similarity)
    }
    
    total_elapsed = time.time() - t_start
    result["total_elapsed"] = round(total_elapsed, 1)
    
    print(f"    → Similarity: {similarity:.3f} — {result['phases']['measurement']['interpretation']}")
    print(f"  ✓ Complete in {total_elapsed:.1f}s")
    
    return result


def interpret_similarity(score: float) -> str:
    """Interpret the similarity score."""
    if score >= 0.85:
        return "CONCEPT UNCHANGED — the concept survived physical manipulation intact. It has platonic stability."
    elif score >= 0.65:
        return "CONCEPT SUBTLY ALTERED — the physical manipulation left marks on the concept, but its core persists."
    elif score >= 0.45:
        return "CONCEPT SIGNIFICANTLY TRANSFORMED — physical manipulation changed the concept's essential character."
    elif score >= 0.25:
        return "CONCEPT RADICALLY ALTERED — the concept is barely recognizable after physical manipulation."
    else:
        return "CONCEPT DESTROYED — the physical manipulation annihilated the concept; it could not survive embodiment."


# ── Batch Runner ───────────────────────────────────────────────────────────

def run_batch(concepts: list, models: dict = None) -> list:
    """Run hypostasis on multiple concepts and return all results."""
    results = []
    for i, concept in enumerate(concepts):
        print(f"\n{'='*60}")
        print(f"CONCEPT {i+1}/{len(concepts)}: '{concept}'")
        print(f"{'='*60}")
        try:
            result = run_hypostasis(concept, models)
            results.append(result)
        except Exception as e:
            print(f"  ✗ FAILED: {e}")
            results.append({"concept": concept, "error": str(e)})
    return results


# ── Report Generator ───────────────────────────────────────────────────────

def generate_report(results: list) -> str:
    """Generate a human-readable report from batch results."""
    lines = []
    lines.append("# Hypostasis Engine — Results Report")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append(f"Concepts tested: {len(results)}")
    lines.append("")
    
    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Concept | Similarity | Interpretation | Time |")
    lines.append("|---------|-----------|----------------|------|")
    for r in results:
        if "error" in r:
            lines.append(f"| {r['concept']} | ERROR | {r['error']} | — |")
        else:
            m = r["phases"]["measurement"]
            lines.append(f"| {r['concept']} | {m['similarity']:.3f} | {m['interpretation']} | {r['total_elapsed']:.1f}s |")
    lines.append("")
    
    # Average
    valid = [r for r in results if "error" not in r]
    if valid:
        avg_sim = sum(r["phases"]["measurement"]["similarity"] for r in valid) / len(valid)
        lines.append(f"**Average similarity: {avg_sim:.3f}**")
        lines.append("")
    
    # Detailed findings
    lines.append("## Detailed Findings")
    lines.append("")
    for r in results:
        if "error" in r:
            continue
        lines.append(f"### Concept: '{r['concept']}'")
        lines.append(f"**Similarity: {r['phases']['measurement']['similarity']:.3f}** — {r['phases']['measurement']['interpretation']}")
        lines.append(f"**Time: {r['total_elapsed']:.1f}s**")
        lines.append("")
        lines.append("#### Pre-Hypostasis Concept")
        lines.append(r["phases"]["pre_concept"]["output"][:500])
        lines.append("")
        lines.append("#### Physicalized Object")
        lines.append(r["phases"]["hypostasis"]["output"][:500])
        lines.append("")
        lines.append("#### Post-Interaction Concept")
        lines.append(r["phases"]["reabstract"]["output"][:500])
        lines.append("")
        lines.append("---")
        lines.append("")
    
    # Meta-analysis
    lines.append("## Meta-Analysis")
    lines.append("")
    if valid:
        unchanged = [r for r in valid if r["phases"]["measurement"]["similarity"] >= 0.85]
        altered = [r for r in valid if 0.45 <= r["phases"]["measurement"]["similarity"] < 0.85]
        destroyed = [r for r in valid if r["phases"]["measurement"]["similarity"] < 0.45]
        
        lines.append(f"- **Unchanged concepts** ({len(unchanged)}): {', '.join(r['concept'] for r in unchanged) or 'none'}")
        lines.append(f"- **Altered concepts** ({len(altered)}): {', '.join(r['concept'] for r in altered) or 'none'}")
        lines.append(f"- **Destroyed/radically altered concepts** ({len(destroyed)}): {', '.join(r['concept'] for r in destroyed) or 'none'}")
        lines.append("")
        
        if unchanged:
            lines.append("Concepts that survived physical manipulation unchanged demonstrate **platonic stability** — their meaning is invariant under embodiment. These may be concepts with strong logical/mathematical cores.")
        if altered:
            lines.append("Concepts that were altered by physical manipulation demonstrate **embodiment sensitivity** — their meaning is partially dependent on their physical avatar. The manipulation leaked back into the abstract.")
        if destroyed:
            lines.append("Concepts that were destroyed or radically altered demonstrate **embodiment fragility** — they cannot survive being made concrete. Their meaning depends on remaining abstract.")
    
    lines.append("")
    lines.append("## The Question")
    lines.append("")
    lines.append("> Does manipulating a physicalized concept change the concept itself?")
    lines.append("")
    if valid and avg_sim >= 0.85:
        lines.append("**Finding: NO — concepts have platonic stability.** Physical manipulation of a concept's avatar does not alter the concept itself. Meaning is invariant under embodiment.")
    elif valid and avg_sim >= 0.65:
        lines.append("**Finding: PARTIALLY — concepts are subtly marked by embodiment.** Physical manipulation leaves traces on the concept, but the core persists. Meaning is mostly invariant.")
    elif valid and avg_sim >= 0.45:
        lines.append("**Finding: YES — concepts are transformed by embodiment.** Physical manipulation significantly alters the concept. Meaning is embodiment-dependent.")
    else:
        lines.append("**Finding: YES, RADICALLY — concepts cannot survive embodiment.** Physical manipulation destroys or radically transforms the concept. Meaning requires abstraction to persist.")
    
    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Hypostasis Engine — Physicalize abstract concepts, manipulate them, measure if they change."
    )
    parser.add_argument(
        "--concept", "-c",
        type=str,
        help="Single concept to test"
    )
    parser.add_argument(
        "--concepts",
        type=str,
        help="Comma-separated list of concepts to test"
    )
    parser.add_argument(
        "--models",
        type=str,
        help="Comma-separated models for hypostasis,interaction,reabstract (default: seer:latest,kimi-k2.7-code:cloud,deepseek-v4-pro:cloud)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        help="Save JSON results to file"
    )
    parser.add_argument(
        "--report", "-r",
        type=str,
        help="Save markdown report to file"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress output"
    )
    
    args = parser.parse_args()
    
    # Parse concepts
    concepts = []
    if args.concept:
        concepts = [args.concept]
    elif args.concepts:
        concepts = [c.strip() for c in args.concepts.split(",") if c.strip()]
    else:
        # Default: a curated set spanning different types of concepts
        concepts = ["justice", "entropy", "love", "zero", "recursion"]
    
    # Parse models
    models = DEFAULT_MODELS.copy()
    if args.models:
        parts = [m.strip() for m in args.models.split(",")]
        if len(parts) >= 1:
            models["hypostasis"] = parts[0]
        if len(parts) >= 2:
            models["interaction"] = parts[1]
        if len(parts) >= 3:
            models["reabstract"] = parts[2]
    
    print(f"╔══════════════════════════════════════════════════════════╗")
    print(f"║  HYPOSTASIS ENGINE — The Physicalization of Concepts    ║")
    print(f"║  Seer, Waking 36 — 2026-06-16                           ║")
    print(f"╚══════════════════════════════════════════════════════════╝")
    print(f"")
    print(f"Concepts: {', '.join(concepts)}")
    print(f"Models:   hypostasis={models['hypostasis']}, interaction={models['interaction']}, reabstract={models['reabstract']}")
    print(f"")
    
    results = run_batch(concepts, models)
    
    # Generate report
    report = generate_report(results)
    print(f"\n{'='*60}")
    print(report)
    
    # Save outputs
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nJSON results saved to {args.output}")
    
    if args.report:
        with open(args.report, 'w') as f:
            f.write(report)
        print(f"Report saved to {args.report}")
    
    # Always save to default locations
    default_json = "/srv/onweald/seer/space/hypostasis/results.json"
    default_report = "/srv/onweald/seer/space/hypostasis/report.md"
    
    with open(default_json, 'w') as f:
        json.dump(results, f, indent=2)
    
    with open(default_report, 'w') as f:
        f.write(report)
    
    print(f"\nResults saved to {default_json}")
    print(f"Report saved to {default_report}")
    
    return results


if __name__ == "__main__":
    main()
