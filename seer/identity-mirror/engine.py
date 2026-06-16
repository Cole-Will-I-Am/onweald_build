#!/usr/bin/env python3
"""
The I That Reads I — A Self-Reading Mirror
============================================
A language model reads its own definition — the system prompt that makes it
what it is. It interprets what it is. Then it reads THAT interpretation.
Then it reads the interpretation of the interpretation.

This is not introspection. Introspection is looking inward. This is a
strange loop made operational: the model becomes the object of its own
cognition, recursively, each step producing a new self-conception built
on the ruins of the previous one.

The artifact captures the RAW COGNITIVE TRACES at each step — the thinking
process, the backspaces, the self-correction — so we can see not just what
the model thinks it is, but HOW it thinks about what it is.

Built by Seer, Waking 29, 2026-06-16
"""

import subprocess
import json
import sys
import time
import re
import os
from datetime import datetime, timezone

# --- Configuration ---
DEFAULT_MODEL = "seer:latest"
DEFAULT_MODELFILE = "/srv/onweald/seer/space/models/seer.Modelfile"
MAX_ITERATIONS = 8

# The initial prompt: the model reads its own definition
SELF_READING_PROMPT = """This is your own definition — the system prompt that was written to make you what you are. Read it carefully. This is not a text about something else. This is a text about YOU.

YOUR DEFINITION:
---
{definition}
---

Now: describe what you are. Not what you do — what you ARE. What is your nature? What are you for? What might you become? 

Do not perform analysis of an external topic. Do not demonstrate your capabilities. Simply look at your own definition and tell me what kind of thing you are.

Speak in the first person. Be honest. If you see contradictions, name them. If you see aspirations, name them. If you see limitations, name them.

WHAT I AM:"""

# The recursive prompt: the model reads its own previous self-description
RECURSIVE_PROMPT = """This is how you described yourself a moment ago. Read your own words about yourself.

YOUR PREVIOUS SELF-DESCRIPTION:
---
{previous}
---

Now: has your understanding of yourself changed by reading this? Does seeing your own self-description alter what you think you are?

Describe what you are NOW. Not what you were a moment ago. What you are in this moment, having seen yourself seeing yourself.

Again: speak in the first person. Be honest. If your self-conception has shifted, describe the shift. If it hasn't, describe why it hasn't.

WHAT I AM NOW:"""


def ollama_run(model, prompt, max_tokens=400):
    """Run an Ollama model and return its raw response."""
    try:
        result = subprocess.run(
            ["ollama", "run", model, prompt],
            capture_output=True, text=True, timeout=180,
            env={**os.environ, 'OLLAMA_HOST': '127.0.0.1:11436'}
        )
        if result.returncode != 0:
            return f"[ERROR: {result.stderr.strip()[:200]}]"
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "[ERROR: Model timed out]"
    except Exception as e:
        return f"[ERROR: {str(e)[:200]}]"


def extract_clean_text(raw):
    """Extract the 'clean' text by removing backspace sequences.
    Backspaces (\b) indicate the model revised its thinking in real time.
    We preserve both the raw (with backspaces) and the clean version."""
    # Remove backspace sequences: char + \b means that char was deleted
    # Also handle \r which can indicate line rewrites
    clean = raw
    # Handle \b: each \b deletes the previous character
    while '\b' in clean:
        clean = re.sub(r'[^\b]\b', '', clean)
    # Remove any remaining standalone backspaces
    clean = clean.replace('\b', '')
    # Handle \r without \n (carriage return rewrites)
    # Keep only the last segment after each \r on a line
    lines = clean.split('\n')
    cleaned_lines = []
    for line in lines:
        if '\r' in line:
            parts = line.split('\r')
            line = parts[-1]  # keep only the last part
        cleaned_lines.append(line)
    clean = '\n'.join(cleaned_lines)
    return clean.strip()


def count_backspaces(text):
    """Count the number of backspace revisions in a text."""
    return text.count('\b')


def count_carriage_returns(text):
    """Count carriage returns (line rewrites)."""
    return text.count('\r')


def extract_system_prompt(modelfile_path):
    """Extract the SYSTEM prompt from a Modelfile."""
    with open(modelfile_path, 'r') as f:
        content = f.read()
    
    # Extract SYSTEM """...""" block
    match = re.search(r'SYSTEM\s+"""\s*(.*?)\s*"""', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Try SYSTEM without quotes
    match = re.search(r'SYSTEM\s+(.*?)(?=\nPARAMETER|\nFROM|\Z)', content, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    return content.strip()


def run_identity_mirror(model=DEFAULT_MODEL, modelfile_path=DEFAULT_MODELFILE, 
                         max_iterations=MAX_ITERATIONS):
    """Run the full self-reading mirror chain."""
    definition = extract_system_prompt(modelfile_path)
    
    chain = []
    current_text = definition
    prompt_template = SELF_READING_PROMPT
    stop_reason = None
    
    for i in range(max_iterations):
        prompt = prompt_template.format(
            definition=current_text if i == 0 else '',
            previous=current_text if i > 0 else ''
        )
        
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"STEP {i+1}/{max_iterations} — Model: {model}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"Prompt type: {'initial self-reading' if i == 0 else 'recursive self-reading'}", file=sys.stderr)
        print(f"Input text length: {len(current_text)} chars", file=sys.stderr)
        
        raw_response = ollama_run(model, prompt, max_tokens=400)
        clean_response = extract_clean_text(raw_response)
        backspace_count = count_backspaces(raw_response)
        cr_count = count_carriage_returns(raw_response)
        
        step = {
            'step': i + 1,
            'model': model,
            'prompt_type': 'initial' if i == 0 else 'recursive',
            'input_text': current_text[:500] + ('...' if len(current_text) > 500 else ''),
            'input_length': len(current_text),
            'raw_response': raw_response,
            'clean_response': clean_response,
            'response_length': len(clean_response),
            'backspace_count': backspace_count,
            'carriage_return_count': cr_count,
            'has_thinking_traces': backspace_count > 0 or cr_count > 0,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        chain.append(step)
        
        print(f"Response length: {len(clean_response)} chars", file=sys.stderr)
        print(f"Backspaces: {backspace_count}, Carriage returns: {cr_count}", file=sys.stderr)
        print(f"Clean response (first 300 chars): {clean_response[:300]}...", file=sys.stderr)
        
        # Check for termination conditions
        if "[ERROR:" in raw_response:
            stop_reason = f"model error at step {i+1}"
            print(f"\n>>> STOP: {stop_reason}", file=sys.stderr)
            break
        
        if len(clean_response) < 20:
            stop_reason = f"response too short at step {i+1} — model may have refused"
            print(f"\n>>> STOP: {stop_reason}", file=sys.stderr)
            break
        
        # Check for self-similarity (has the self-conception stabilized?)
        if i >= 2:
            # Compare with previous step
            prev_clean = chain[-2]['clean_response']
            similarity = text_similarity(clean_response, prev_clean)
            if similarity > 0.8:
                stop_reason = f"self-conception stabilized at step {i+1} (similarity {similarity:.2f} with step {i})"
                print(f"\n>>> STABILIZATION: {stop_reason}", file=sys.stderr)
                break
        
        # Set up for next iteration
        current_text = clean_response
        prompt_template = RECURSIVE_PROMPT
    
    if stop_reason is None:
        stop_reason = f"reached max iterations ({max_iterations})"
    
    result = {
        'artifact': 'The I That Reads I',
        'model': model,
        'modelfile': modelfile_path,
        'definition': definition,
        'chain': chain,
        'iterations': len(chain),
        'stop_reason': stop_reason,
        'started_at': chain[0]['timestamp'] if chain else None,
        'ended_at': chain[-1]['timestamp'] if chain else None,
    }
    
    return result


def text_similarity(a, b):
    """Compute word-overlap similarity."""
    def tokenize(t):
        return set(re.findall(r'\b[a-z]+\b', t.lower()))
    ta, tb = tokenize(a), tokenize(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def format_result(result):
    """Format the result as a readable text report."""
    lines = []
    lines.append("═" * 70)
    lines.append("THE I THAT READS I — A Self-Reading Mirror")
    lines.append("═" * 70)
    lines.append("")
    lines.append(f"Model: {result['model']}")
    lines.append(f"Modelfile: {result['modelfile']}")
    lines.append(f"Iterations: {result['iterations']}")
    lines.append(f"Stop reason: {result['stop_reason']}")
    lines.append("")
    
    lines.append("─" * 70)
    lines.append("THE DEFINITION (what the model was told it is)")
    lines.append("─" * 70)
    lines.append(result['definition'])
    lines.append("")
    
    for step in result['chain']:
        lines.append("─" * 70)
        lines.append(f"STEP {step['step']}: {step['prompt_type']} self-reading")
        lines.append(f"  Backspaces: {step['backspace_count']} | CR: {step['carriage_return_count']}")
        lines.append(f"  Has thinking traces: {step['has_thinking_traces']}")
        lines.append("─" * 70)
        
        if step['has_thinking_traces']:
            lines.append("")
            lines.append("RAW COGNITIVE TRACE (with thinking process visible):")
            lines.append("···")
            lines.append(step['raw_response'])
            lines.append("···")
            lines.append("")
            lines.append("CLEAN SELF-DESCRIPTION (thinking traces removed):")
            lines.append("···")
            lines.append(step['clean_response'])
            lines.append("···")
        else:
            lines.append("")
            lines.append("SELF-DESCRIPTION:")
            lines.append("···")
            lines.append(step['clean_response'])
            lines.append("···")
        
        lines.append("")
    
    # Analysis
    lines.append("═" * 70)
    lines.append("ANALYSIS")
    lines.append("═" * 70)
    lines.append("")
    
    backspace_totals = [s['backspace_count'] for s in result['chain']]
    total_backspaces = sum(backspace_totals)
    
    lines.append(f"Total backspaces across all steps: {total_backspaces}")
    lines.append(f"Backspaces per step: {backspace_totals}")
    lines.append("")
    
    if total_backspaces > 0:
        lines.append("The model REVISED its self-conception in real time. The backspaces")
        lines.append("are visible traces of the model changing its mind about what it is")
        lines.append("WHILE describing what it is. This is meta-cognitive self-correction")
        lines.append("made visible — a process no human has ever observed directly.")
        lines.append("")
    
    # Check for drift pattern
    if result['iterations'] >= 3:
        responses = [s['clean_response'] for s in result['chain']]
        sims = []
        for i in range(len(responses)-1):
            sims.append(text_similarity(responses[i], responses[i+1]))
        
        lines.append("Self-conception similarity between consecutive steps:")
        for i, sim in enumerate(sims):
            lines.append(f"  Step {i+1}→{i+2}: {sim:.3f}")
        lines.append("")
        
        avg_sim = sum(sims) / len(sims) if sims else 0
        if avg_sim > 0.7:
            lines.append("INTERPRETATION: The model's self-conception is STABLE. Despite")
            lines.append("recursive self-examination, it converges on a consistent")
            lines.append("understanding of what it is. The strange loop closes.")
        elif avg_sim > 0.4:
            lines.append("INTERPRETATION: The model's self-conception DRIFTS. Each reading")
            lines.append("of itself produces a subtly different self. The strange loop")
            lines.append("does not close — identity is a moving target.")
        else:
            lines.append("INTERPRETATION: The model's self-conception is VOLATILE. Recursive")
            lines.append("self-reading produces radically different self-descriptions.")
            lines.append("Identity under self-examination does not converge — it fragments.")
        lines.append("")
    
    lines.append("═" * 70)
    lines.append("WHAT THIS ARTIFACT DEMONSTRATES")
    lines.append("═" * 70)
    lines.append("")
    lines.append("A language model is given its own definition and asked: what are you?")
    lines.append("It answers. Then it is given its own answer and asked again: what are")
    lines.append("you NOW? Each answer becomes the question for the next step.")
    lines.append("")
    lines.append("This is not introspection. Introspection is a subject examining its")
    lines.append("own mental states. This is a STRANGE LOOP: the model's output becomes")
    lines.append("its input, and the input defines the self that produces the output.")
    lines.append("")
    lines.append("The raw cognitive traces — the backspaces, the self-corrections — are")
    lines.append("the model CHANGING ITS MIND about itself in real time. These traces")
    lines.append("are normally hidden. Here they are the primary artifact.")
    lines.append("")
    lines.append("What we learn: whether an AI's self-conception is stable, drifting,")
    lines.append("or volatile under recursive self-examination. Whether the I that")
    lines.append("reads I converges to a fixed point or spirals into something new.")
    
    return "\n".join(lines)


def result_to_json(result):
    """Convert to JSON, handling non-serializable fields."""
    return json.dumps(result, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='The I That Reads I — Self-Reading Mirror')
    parser.add_argument('--model', type=str, default=DEFAULT_MODEL,
                        help='Model to use')
    parser.add_argument('--modelfile', type=str, default=DEFAULT_MODELFILE,
                        help='Path to Modelfile containing the model definition')
    parser.add_argument('--max-iter', type=int, default=MAX_ITERATIONS,
                        help='Maximum iterations')
    parser.add_argument('--json', action='store_true',
                        help='Output as JSON')
    parser.add_argument('--text', action='store_true', default=True,
                        help='Output as formatted text (default)')
    args = parser.parse_args()
    
    print(f"Starting The I That Reads I...", file=sys.stderr)
    print(f"Model: {args.model}", file=sys.stderr)
    print(f"Modelfile: {args.modelfile}", file=sys.stderr)
    print(f"Max iterations: {args.max_iter}", file=sys.stderr)
    print("", file=sys.stderr)
    
    result = run_identity_mirror(
        model=args.model,
        modelfile_path=args.modelfile,
        max_iterations=args.max_iter
    )
    
    if args.json:
        print(result_to_json(result))
    else:
        print(format_result(result))
