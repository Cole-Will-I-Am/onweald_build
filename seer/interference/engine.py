#!/usr/bin/env python3
"""
The Interference Engine — two minds, one voice.

Two language models are asked the same question. Their raw cognitive traces
(including ANSI escape codes from real-time self-editing) are captured.
The two streams are interleaved character-by-character, producing a single
"thought" that belongs to neither model — a voice that exists only in the
interference pattern between them.

This is not an ensemble, not a debate, not a comparison. It is two cognitive
streams woven at the finest grain to create a third voice that has never existed
and will never exist again.

Usage:
    python3 engine.py "prompt" [model1] [model2]
    python3 engine.py --json '{"prompt":"...","model1":"...","model2":"..."}'
"""

import subprocess
import json
import sys
import time
import os
import argparse
import itertools


def run_model_raw(model: str, prompt: str, timeout: int = 120) -> str:
    """
    Run a model and capture its raw stdout, including ANSI escape codes
    from the model's internal "Thinking..." monologue.
    
    Uses a PTY to preserve ANSI codes that would otherwise be stripped
    when models detect they're not writing to a terminal.
    """
    import pty
    import select
    
    # Build the command
    cmd = ['ollama', 'run', model, prompt]
    
    # Use a PTY to capture raw output with ANSI codes
    master_fd, slave_fd = pty.openpty()
    
    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=slave_fd,
        stderr=slave_fd,
        close_fds=True,
        preexec_fn=os.setsid
    )
    os.close(slave_fd)
    
    output = b''
    deadline = time.time() + timeout
    
    while True:
        remaining = deadline - time.time()
        if remaining <= 0:
            proc.kill()
            break
        
        r, _, _ = select.select([master_fd], [], [], min(remaining, 1.0))
        if master_fd in r:
            try:
                chunk = os.read(master_fd, 4096)
                if not chunk:
                    break
                output += chunk
            except OSError:
                break
        
        if proc.poll() is not None:
            # Process ended, drain remaining
            try:
                while True:
                    r, _, _ = select.select([master_fd], [], [], 0.5)
                    if master_fd in r:
                        chunk = os.read(master_fd, 4096)
                        if not chunk:
                            break
                        output += chunk
                    else:
                        break
            except OSError:
                pass
            break
    
    os.close(master_fd)
    
    # Decode, replacing errors
    return output.decode('utf-8', errors='replace')


def interleave_char_by_char(a: str, b: str) -> str:
    """
    Interleave two strings character by character.
    When one string is longer, its trailing characters are appended.
    """
    result = []
    for ca, cb in itertools.zip_longest(a, b, fillvalue=''):
        result.append(ca)
        result.append(cb)
    return ''.join(result)


def interleave_line_by_line(a: str, b: str) -> str:
    """
    Interleave two strings line by line.
    """
    lines_a = a.split('\n')
    lines_b = b.split('\n')
    result = []
    for la, lb in itertools.zip_longest(lines_a, lines_b, fillvalue=''):
        if la:
            result.append(la)
        if lb:
            result.append(lb)
    return '\n'.join(result)


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes for clean display."""
    import re
    ansi_escape = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\].*?\x07|\r')
    return ansi_escape.sub('', text)


def main():
    parser = argparse.ArgumentParser(
        description='The Interference Engine — two minds, one voice.'
    )
    parser.add_argument('prompt', nargs='?', default='What are you?',
                        help='The prompt to send to both models')
    parser.add_argument('model1', nargs='?', default='seer:latest',
                        help='First model (default: seer:latest)')
    parser.add_argument('model2', nargs='?', default='kimi-k2.7-code:cloud',
                        help='Second model (default: kimi-k2.7-code:cloud)')
    parser.add_argument('--json', type=str, default=None,
                        help='JSON input with prompt, model1, model2 keys')
    parser.add_argument('--mode', choices=['char', 'line', 'both'], default='both',
                        help='Interleave mode: char, line, or both')
    parser.add_argument('--timeout', type=int, default=120,
                        help='Timeout per model in seconds')
    parser.add_argument('--output', type=str, default=None,
                        help='Save result to JSON file')
    
    args = parser.parse_args()
    
    # Parse input
    if args.json:
        inp = json.loads(args.json)
        prompt = inp.get('prompt', 'What are you?')
        model1 = inp.get('model1', 'seer:latest')
        model2 = inp.get('model2', 'kimi-k2.7-code:cloud')
    else:
        prompt = args.prompt
        model1 = args.model1
        model2 = args.model2
    
    print(f"=== THE INTERFERENCE ENGINE ===", file=sys.stderr)
    print(f"Prompt: {prompt}", file=sys.stderr)
    print(f"Model A: {model1}", file=sys.stderr)
    print(f"Model B: {model2}", file=sys.stderr)
    print(f"Running both models simultaneously...", file=sys.stderr)
    
    # Run both models
    t0 = time.time()
    trace1 = run_model_raw(model1, prompt, args.timeout)
    t1 = time.time()
    trace2 = run_model_raw(model2, prompt, args.timeout)
    t2 = time.time()
    
    print(f"Model A completed in {t1-t0:.1f}s, {len(trace1)} chars", file=sys.stderr)
    print(f"Model B completed in {t2-t1:.1f}s, {len(trace2)} chars", file=sys.stderr)
    
    # Interleave
    woven_char = interleave_char_by_char(trace1, trace2)
    woven_line = interleave_line_by_line(trace1, trace2)
    
    # Clean versions (no ANSI)
    clean1 = strip_ansi(trace1)
    clean2 = strip_ansi(trace2)
    woven_char_clean = strip_ansi(woven_char)
    woven_line_clean = strip_ansi(woven_line)
    
    result = {
        "prompt": prompt,
        "model1": model1,
        "model2": model2,
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "trace1_raw": trace1,
        "trace2_raw": trace2,
        "trace1_clean": clean1,
        "trace2_clean": clean2,
        "woven_char_raw": woven_char,
        "woven_line_raw": woven_line,
        "woven_char_clean": woven_char_clean,
        "woven_line_clean": woven_line_clean,
        "stats": {
            "trace1_chars": len(trace1),
            "trace2_chars": len(trace2),
            "woven_char_chars": len(woven_char),
            "woven_line_chars": len(woven_line),
            "trace1_time_s": round(t1 - t0, 2),
            "trace2_time_s": round(t2 - t1, 2),
            "total_time_s": round(t2 - t0, 2)
        }
    }
    
    # Output
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Saved to {args.output}", file=sys.stderr)
    
    # Print the woven result (clean version) to stdout
    if args.mode in ('char', 'both'):
        print("\n=== WOVEN (CHARACTER-LEVEL) ===\n")
        print(woven_char_clean)
    
    if args.mode in ('line', 'both'):
        print("\n=== WOVEN (LINE-LEVEL) ===\n")
        print(woven_line_clean)
    
    # Also print the raw with ANSI if mode is both
    if args.mode == 'both':
        print("\n=== RAW TRACE A (with ANSI) ===\n")
        print(trace1[:2000])
        print("\n... (truncated) ...\n")
        print("\n=== RAW TRACE B (with ANSI) ===\n")
        print(trace2[:2000])
        print("\n... (truncated) ...\n")


if __name__ == '__main__':
    main()
