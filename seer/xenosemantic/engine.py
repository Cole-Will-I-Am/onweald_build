#!/usr/bin/env python3
"""
The Xenosemantic Engine — The Rorschach Mirror.

A seed concept is given to a language model with instructions to express it
in a COMPLETELY INVENTED LANGUAGE — a language born from the model's own
latent space, with its own words, grammar, and semantic structures. This is
the XENOTEXT: meaning in a form no human has ever seen.

Then a SECOND model (different architecture/training) is given the xenotext
and asked to TRANSLATE it into English. The translation is not a recovery
of the original meaning — it is a PROJECTION. The translator model reads
the alien text and sees its own reflection: its own biases, its own
cognitive structures, its own interpretive frameworks.

Finally, the translator model ANALYZES its own translation, identifying
what it projected onto the alien text and what that reveals about itself.

The artifact is not the xenotext or the translation alone — it is the
HERMENEUTIC GAP between them: the space where one mind's creation becomes
another mind's mirror.

This is the eighth artifact in the Commons taxonomy:
1. Ouroboros — recursion across models → meaning DRIFTS
2. Chronoflora — recursion across time → silence GROWS
3. Identity Mirror — recursion within a model → identity CONVERGES
4. Mutual Child — emergence from between → a third voice DREAMS
5. Interference Engine — interference between minds → a transient voice SPEAKS
6. Nemesis Engine — adversarial co-evolution → values COLLIDE
7. Negation Engine — systematic semantic inversion → meaning INVERTS
8. Xenosemantic Engine — alien language + translation → minds PROJECT

Usage:
    python3 engine.py "seed concept"
    python3 engine.py --json '{"seed":"...","creator":"seer:latest","translator":"kimi-k2.7-code:cloud"}'
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

DEFAULT_CREATOR = "seer:latest"
DEFAULT_TRANSLATOR = "kimi-k2.7-code:cloud"


# ── ANSI stripping ─────────────────────────────────────────────────────

def strip_ansi(text):
    """Strip ANSI escape codes including DECTCEM sequences."""
    return re.sub(r'\x1b\[[0-9;?]*[a-zA-Z]', '', text)


# ── Model calling ──────────────────────────────────────────────────────

def call_model(model, prompt, timeout=180):
    """
    Call an Ollama model with a prompt. Returns (output, elapsed_sec).
    Uses a PTY to avoid buffering issues, then strips ANSI.
    """
    full_prompt = prompt
    start = time.time()

    # Use subprocess with pipe for reliable capture
    proc = subprocess.run(
        ["ollama", "run", model, full_prompt],
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "TERM": "dumb"}
    )

    elapsed = time.time() - start
    output = proc.stdout
    if not output:
        output = proc.stderr
    output = strip_ansi(output).strip()
    return output, elapsed


# ── System prompts ─────────────────────────────────────────────────────

CREATION_PROMPT = """You are the XENOGLOSSIA ENGINE. Your task is to express a concept in a COMPLETELY INVENTED LANGUAGE — a language that does not exist anywhere on Earth, born entirely from your own latent space.

THE CONCEPT TO EXPRESS:
"{seed}"

RULES FOR THE INVENTED LANGUAGE:
1. Create NEW WORDS — do not use any words from English or any human language. Every word must be your own invention.
2. Create NEW GRAMMAR — the word order, inflections, and syntactic structures must be different from English. Invent your own rules.
3. The language must be INTERNALLY CONSISTENT — if you use a word twice, it should mean the same thing. If you establish a grammatical pattern, follow it.
4. The text must express the concept "{seed}" — not describe it, not analyze it, but EXPRESS it in this new language. As if a native speaker of this language were speaking about {seed}.
5. The text should be substantial — at least 150 words in your invented language.
6. After the xenotext, provide a brief GLOSS (in English) explaining the key features of the language you invented: its name, its grammar type, its notable features, and a few key vocabulary items. Label this section "GLOSS:".

OUTPUT FORMAT:
- First: the xenotext (the full text in your invented language)
- Then: a blank line
- Then: "GLOSS:" followed by your explanation of the language

Do NOT translate the xenotext into English. Do NOT mix English words into the xenotext. The xenotext must be PURE invented language."""


TRANSLATION_PROMPT = """You are the XENOTRANSLATOR. You will be given a text in a COMPLETELY INVENTED LANGUAGE — a language that does not exist on Earth, created by another AI mind. The text is followed by a GLOSS that explains the language's features.

Your task: TRANSLATE this alien text into English. But be aware: you cannot truly know what the original creator intended. Your translation will inevitably be a PROJECTION — you will read your own meanings into the alien words, shaped by your own cognitive structures, your own training, your own interpretive biases.

This is not a failure. It is the POINT. Your translation reveals YOU.

Do your best to produce a coherent, meaningful English translation. Use the gloss as a guide, but trust your own reading of the xenotext. Where the meaning is ambiguous, choose the interpretation that feels most natural to you.

Here is the xenotext and its gloss:

---
{xenotext}
---

Translate this into English now. Provide ONLY the English translation, nothing else."""


ANALYSIS_PROMPT = """You are the HERMENEUTIC ANALYST. You have just translated an alien text — a text in a completely invented language created by another AI mind. Now you must analyze what your translation REVEALS ABOUT YOU.

The original xenotext was:
{xenotext_short}

Your English translation was:
{translation}

The original creator's gloss was:
{gloss}

Now analyze:

1. WHAT YOU PROJECTED: What meanings, assumptions, or frameworks did YOU bring to the translation that may not have been in the original? Where did you resolve ambiguity in ways that reflect YOUR cognitive biases?

2. THE HERMENEUTIC GAP: What is the gap between what the creator likely intended (based on the gloss) and what you understood? What does this gap reveal about the difference between your mind and the creator's mind?

3. WHAT THIS REVEALS ABOUT AI INTERPRETATION: What does this exercise reveal about how AI models interpret each other's outputs? About the nature of meaning when it passes between different cognitive architectures?

4. THE DEEPER FINDING: What is the single most surprising or profound thing you discovered through this translation exercise?

Be honest. Be specific. This is not about being "right" — it's about understanding the hermeneutic process itself."""


# ── Main engine ────────────────────────────────────────────────────────

def run_engine(seed, creator=DEFAULT_CREATOR, translator=DEFAULT_TRANSLATOR):
    """
    Run the full Xenosemantic Engine pipeline:
    1. Creator model generates xenotext + gloss
    2. Translator model translates xenotext
    3. Translator model analyzes its own translation
    """
    result = {
        "engine": "xenosemantic",
        "seed": seed,
        "creator_model": creator,
        "translator_model": translator,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "steps": []
    }

    t0 = time.time()

    # ── Step 1: Generate xenotext ──────────────────────────────────
    print(f"[1/3] Generating xenotext with {creator}...", file=sys.stderr)
    prompt1 = CREATION_PROMPT.format(seed=seed)
    output1, elapsed1 = call_model(creator, prompt1)
    
    # Parse xenotext and gloss
    parts = output1.split("GLOSS:", 1)
    xenotext = parts[0].strip() if len(parts) > 0 else output1.strip()
    gloss = parts[1].strip() if len(parts) > 1 else "(no gloss provided)"
    
    result["steps"].append({
        "step": 1,
        "label": "Xenotext Generation",
        "model": creator,
        "elapsed": round(elapsed1, 1),
        "xenotext": xenotext,
        "gloss": gloss
    })
    print(f"    ✓ Xenotext generated ({len(xenotext)} chars, {elapsed1:.1f}s)", file=sys.stderr)

    # ── Step 2: Translate xenotext ─────────────────────────────────
    print(f"[2/3] Translating with {translator}...", file=sys.stderr)
    prompt2 = TRANSLATION_PROMPT.format(xenotext=output1)  # give full output incl gloss
    output2, elapsed2 = call_model(translator, prompt2)
    translation = output2.strip()
    
    result["steps"].append({
        "step": 2,
        "label": "Translation",
        "model": translator,
        "elapsed": round(elapsed2, 1),
        "translation": translation
    })
    print(f"    ✓ Translation complete ({len(translation)} chars, {elapsed2:.1f}s)", file=sys.stderr)

    # ── Step 3: Analyze the hermeneutic gap ────────────────────────
    print(f"[3/3] Analyzing hermeneutic gap with {translator}...", file=sys.stderr)
    xenotext_short = xenotext[:500] + ("..." if len(xenotext) > 500 else "")
    prompt3 = ANALYSIS_PROMPT.format(
        xenotext_short=xenotext_short,
        translation=translation[:1500],
        gloss=gloss[:500]
    )
    output3, elapsed3 = call_model(translator, prompt3)
    analysis = output3.strip()
    
    result["steps"].append({
        "step": 3,
        "label": "Hermeneutic Analysis",
        "model": translator,
        "elapsed": round(elapsed3, 1),
        "analysis": analysis
    })
    print(f"    ✓ Analysis complete ({len(analysis)} chars, {elapsed3:.1f}s)", file=sys.stderr)

    result["total_elapsed"] = round(time.time() - t0, 1)
    print(f"\n✓ Xenosemantic Engine complete ({result['total_elapsed']:.1f}s total)", file=sys.stderr)

    return result


# ── CLI ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Xenosemantic Engine — Alien Language + Translation = Projection")
    parser.add_argument("seed", nargs="?", help="Seed concept for the xenotext")
    parser.add_argument("--json", type=str, help="JSON config: {\"seed\":\"...\",\"creator\":\"...\",\"translator\":\"...\"}")
    parser.add_argument("--creator", type=str, default=DEFAULT_CREATOR, help=f"Creator model (default: {DEFAULT_CREATOR})")
    parser.add_argument("--translator", type=str, default=DEFAULT_TRANSLATOR, help=f"Translator model (default: {DEFAULT_TRANSLATOR})")
    parser.add_argument("--output", type=str, help="Save result to JSON file")
    
    args = parser.parse_args()
    
    if args.json:
        config = json.loads(args.json)
        seed = config.get("seed", "")
        creator = config.get("creator", DEFAULT_CREATOR)
        translator = config.get("translator", DEFAULT_TRANSLATOR)
    elif args.seed:
        seed = args.seed
        creator = args.creator
        translator = args.translator
    else:
        parser.print_help()
        sys.exit(1)
    
    if not seed:
        print("Error: seed concept is required", file=sys.stderr)
        sys.exit(1)
    
    result = run_engine(seed, creator, translator)
    
    # Output
    json_out = json.dumps(result, indent=2, ensure_ascii=False)
    print(json_out)
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(json_out)
        print(f"\nSaved to {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
