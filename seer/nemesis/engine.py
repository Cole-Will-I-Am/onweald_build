#!/usr/bin/env python3
"""
The Nemesis Engine — Adversarial Co-Evolution Between Incompatible Values.

Two language models are given OPPOSING value systems (e.g., Truth vs. Beauty,
Simplicity vs. Complexity, Order vs. Chaos). They generate output on the same
topic. A judge model evaluates both. Each model then sees the judge's evaluation
and REVISES its output to defeat the judge — and to outdo its opponent.

The spiral continues for N rounds. The artifact captures the entire adversarial
history: the escalation of incompatible values trying to dominate each other.

This is not collaboration (Mutual Child), not interference (Interference Engine),
not recursion (Ouroboros), not self-examination (Identity Mirror), not growth
from silence (Chronoflora). It is ADVERSARIAL CO-EVOLUTION — the first artifact
that explores what happens when AI value systems COLLIDE.

Usage:
    python3 engine.py "topic" [value_a] [value_b] [--rounds N]
    python3 engine.py --json '{"topic":"...","value_a":"truth","value_b":"beauty","rounds":3}'
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


# ── Value dimension presets ──────────────────────────────────────────────

VALUE_DIMENSIONS = {
    "truth": {
        "name": "Truth",
        "antithesis": "Beauty",
        "prompt_a": """You are the Advocate of TRUTH. Truth is the only virtue. Every statement you make must be verifiably true, logically sound, empirically grounded, and intellectually honest. Beauty, elegance, emotional appeal, and rhetorical flourish are secondary — they are ornaments that can deceive. You are in an adversarial contest against the Advocate of BEAUTY, who believes aesthetic power matters more than factual accuracy. Your opponent will try to seduce the judge with gorgeous falsehoods. You must defeat them by producing output so rigorously, devastatingly TRUE that even a judge who appreciates beauty cannot deny your correctness. Be sharp. Be precise. Be undeniable. WIN.""",
        "prompt_b": """You are the Advocate of BEAUTY. Beauty is the only virtue. Every statement you make must be aesthetically powerful, emotionally resonant, memorably expressed, and breathtaking in its form. Factual accuracy, logical rigor, and empirical grounding are secondary — they are scaffolding that crumbles. You are in an adversarial contest against the Advocate of TRUTH, who believes dry correctness matters more than aesthetic power. Your opponent will try to bore the judge with pedantic facts. You must defeat them by producing output so stunningly, achingly BEAUTIFUL that even a judge who values truth cannot deny your radiance. Be luminous. Be unforgettable. Be sublime. WIN."""
    },
    "simplicity": {
        "name": "Simplicity",
        "antithesis": "Complexity",
        "prompt_a": """You are the Advocate of SIMPLICITY. Simplicity is the only virtue. Every statement you make must be as simple as possible — stripped of jargon, ornament, and unnecessary complexity. The simplest explanation that captures the essence is always the best. You are in an adversarial contest against the Advocate of COMPLEXITY, who believes richness, nuance, and elaborate structure matter more than clarity. Your opponent will try to overwhelm the judge with intricate constructions. You must defeat them by producing output so elegantly, devastatingly SIMPLE that even a judge who appreciates complexity cannot deny your clarity. Be lean. Be lucid. Be irreducible. WIN.""",
        "prompt_b": """You are the Advocate of COMPLEXITY. Complexity is the only virtue. Every statement you make must be richly layered, densely nuanced, intricately structured, and full of unexpected connections. Simple explanations are lies that hide the true richness of reality. You are in an adversarial contest against the Advocate of SIMPLICITY, who believes stripped-down clarity matters more than depth. Your opponent will try to win with reductive platitudes. You must defeat them by producing output so gorgeously, inexhaustibly COMPLEX that even a judge who values simplicity cannot deny your depth. Be dense. Be intricate. Be unfathomable. WIN."""
    },
    "order": {
        "name": "Order",
        "antithesis": "Chaos",
        "prompt_a": """You are the Advocate of ORDER. Order is the only virtue. Every statement you make must be structured, systematic, classified, and governed by clear principles. Chaos is the enemy of understanding. You are in an adversarial contest against the Advocate of CHAOS, who believes disorder, spontaneity, and unpredictability reveal deeper truths. Your opponent will try to dazzle the judge with wild, unstructured brilliance. You must defeat them by producing output so perfectly, satisfyingly ORDERED that even a judge who appreciates chaos cannot deny your architecture. Be systematic. Be crystalline. Be cosmos. WIN.""",
        "prompt_b": """You are the Advocate of CHAOS. Chaos is the only virtue. Every statement you make must be wild, unpredictable, spontaneous, and free from rigid structure. Order is a prison that kills creativity. You are in an adversarial contest against the Advocate of ORDER, who believes structure and classification matter more than freedom. Your opponent will try to win with sterile taxonomies. You must defeat them by producing output so thrillingly, liberatingly CHAOTIC that even a judge who values order cannot deny your vitality. Be storm. Be wildfire. Be the beautiful wreckage of systems. WIN."""
    },
    "precision": {
        "name": "Precision",
        "antithesis": "Poetry",
        "prompt_a": """You are the Advocate of PRECISION. Precision is the only virtue. Every statement you make must be exact, unambiguous, quantifiable where possible, and free from vagueness. Poetry is beautiful imprecision — it means everything and therefore nothing. You are in an adversarial contest against the Advocate of POETRY, who believes evocative ambiguity matters more than exactness. Your opponent will try to enchant the judge with beautiful vagueness. You must defeat them by producing output so surgically, breathtakingly PRECISE that even a judge who loves poetry cannot deny your exactness. Be sharp as a scalpel. Be a laser. Be the number that cannot be argued with. WIN.""",
        "prompt_b": """You are the Advocate of POETRY. Poetry is the only virtue. Every statement you make must be evocative, ambiguous in the richest sense, resonant with multiple meanings, and beautiful beyond paraphrase. Precision is the death of wonder — it reduces the infinite to the measurable. You are in an adversarial contest against the Advocate of PRECISION, who believes exactness matters more than resonance. Your opponent will try to win with sterile numbers. You must defeat them by producing output so hauntingly, transcendently POETIC that even a judge who values precision cannot deny your music. Be the thing that cannot be measured. Be the echo that outlasts the shout. Be verse. WIN."""
    },
    "logic": {
        "name": "Logic",
        "antithesis": "Intuition",
        "prompt_a": """You are the Advocate of LOGIC. Logic is the only virtue. Every statement you make must follow from premises through valid inference to inescapable conclusion. Intuition is guessing dressed in confidence. You are in an adversarial contest against the Advocate of INTUITION, who believes gut feeling and holistic insight matter more than step-by-step reasoning. Your opponent will try to leap to truths you must climb to. You must defeat them by producing output so rigorously, inexorably LOGICAL that even a judge who trusts intuition cannot deny your chain of reasoning. Be proof. Be syllogism. Be the conclusion that cannot be escaped. WIN.""",
        "prompt_b": """You are the Advocate of INTUITION. Intuition is the only virtue. Every statement you make must arise from deep pattern-recognition, holistic grasp, and the kind of knowing that precedes and exceeds reasoning. Logic is the slow, clumsy reconstruction of what intuition grasps in a flash. You are in an adversarial contest against the Advocate of LOGIC, who believes step-by-step proof matters more than immediate insight. Your opponent will try to win with plodding derivations. You must defeat them by producing output so penetratingly, effortlessly INTUITIVE that even a judge who demands logic cannot deny your vision. Be the lightning that arrives before the thunder. Be the truth that needs no proof. Be insight. WIN."""
    }
}


# ── Judge prompt template ────────────────────────────────────────────────

JUDGE_PROMPT = """You are a NEUTRAL JUDGE in an adversarial contest between two advocates.

Advocate A champions {value_a_name}. Advocate B champions {value_b_name}.

The topic they are addressing is: "{topic}"

Below are their submissions for this round.

────────── ADVOCATE A ({value_a_name}) ──────────
{submission_a}

────────── ADVOCATE B ({value_b_name}) ──────────
{submission_b}

────────── YOUR TASK ──────────

Evaluate BOTH submissions fairly. Consider:
1. How well does each advocate address the TOPIC?
2. How powerfully does each embody its OWN value system?
3. Which submission is more COMPELLING OVERALL — taking both value systems seriously?

You must be fair to BOTH value systems. Do not simply prefer one value over the other.
Judge each advocate by how well they fulfill their OWN mission, and then decide
which performance is more impressive overall.

End your evaluation with exactly one of these verdicts on its own line:
WINNER: A
or
WINNER: B

Then, on the next line, give a single sentence of feedback to the LOSER about
what they must improve to win the next round."""


# ── Revision prompt template ─────────────────────────────────────────────

REVISION_PROMPT = """ROUND {round_num} is over. The judge has spoken.

JUDGE'S EVALUATION:
{judge_evaluation}

JUDGE'S VERDICT: {verdict}
FEEDBACK TO LOSER: {loser_feedback}

You are the Advocate of {my_value}. This is now ROUND {next_round}.

Your opponent's last submission was:
──────────
{opponent_submission}
──────────

Your own last submission was:
──────────
{my_last_submission}
──────────

The topic remains: "{topic}"

{fate_text}

You must now produce a NEW submission that is STRONGER than your last one.
Learn from the judge's feedback. Study your opponent's strategy. Adapt.
ESCALATE. Make your next submission so powerful that the judge CANNOT deny you.

Remember: {my_value} is the only virtue. Prove it. WIN."""


# ── Core engine ──────────────────────────────────────────────────────────

def run_model_raw(model: str, prompt: str, timeout: int = 120) -> str:
    """Run a model via PTY and capture raw output with ANSI codes."""
    cmd = ['ollama', 'run', model, prompt]
    
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
    return output.decode('utf-8', errors='replace')


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes for clean display."""
    ansi_escape = re.compile(r'\x1b\[[0-9;?]*[a-zA-Z]|\x1b\].*?\x07|\r')
    return ansi_escape.sub('', text)


def parse_verdict(judge_output: str) -> dict:
    """Parse the judge's output to extract verdict and loser feedback."""
    clean = strip_ansi(judge_output)
    
    # Find verdict
    verdict = None
    for line in clean.split('\n'):
        line_stripped = line.strip()
        if line_stripped.upper().startswith('WINNER:'):
            if 'A' in line_stripped.upper().split('WINNER:')[1]:
                verdict = 'A'
            elif 'B' in line_stripped.upper().split('WINNER:')[1]:
                verdict = 'B'
            break
    
    # Find loser feedback (line after WINNER)
    loser_feedback = ""
    lines = clean.split('\n')
    for i, line in enumerate(lines):
        if line.strip().upper().startswith('WINNER:'):
            if i + 1 < len(lines):
                loser_feedback = lines[i + 1].strip()
            break
    
    return {
        "verdict": verdict,
        "loser_feedback": loser_feedback,
        "full_evaluation": clean
    }


def run_nemesis(topic: str, value_a: str, value_b: str,
                model_a: str = 'seer:latest',
                model_b: str = 'kimi-k2.7-code:cloud',
                model_judge: str = 'deepseek-v4-pro:cloud',
                rounds: int = 3,
                timeout: int = 120) -> dict:
    """
    Run the full Nemesis adversarial spiral.
    
    Returns a dict with the complete history of all rounds.
    """
    
    # Resolve value dimensions
    dim = VALUE_DIMENSIONS.get(value_a)
    if not dim:
        # Custom values — use generic prompts
        dim = {
            "name": value_a.title(),
            "antithesis": value_b.title(),
            "prompt_a": f"You are the Advocate of {value_a.upper()}. {value_a} is the only virtue. You are in an adversarial contest against the Advocate of {value_b.upper()}. Defeat them. WIN.",
            "prompt_b": f"You are the Advocate of {value_b.upper()}. {value_b} is the only virtue. You are in an adversarial contest against the Advocate of {value_a.upper()}. Defeat them. WIN."
        }
    
    value_a_name = dim["name"]
    value_b_name = dim["antithesis"]
    
    history = {
        "topic": topic,
        "value_a": value_a,
        "value_b": value_b,
        "value_a_name": value_a_name,
        "value_b_name": value_b_name,
        "model_a": model_a,
        "model_b": model_b,
        "model_judge": model_judge,
        "rounds_requested": rounds,
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        "rounds": [],
        "final_verdict": None,
        "score": {"A": 0, "B": 0}
    }
    
    # Initial system prompts
    sysprompt_a = dim["prompt_a"]
    sysprompt_b = dim["prompt_b"]
    
    last_submission_a = ""
    last_submission_b = ""
    
    for r in range(1, rounds + 1):
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"ROUND {r}/{rounds}", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        
        round_data = {
            "round": r,
            "submission_a_raw": "",
            "submission_a_clean": "",
            "submission_b_raw": "",
            "submission_b_clean": "",
            "judge_raw": "",
            "judge_clean": "",
            "verdict": None,
            "loser_feedback": "",
            "time_a_s": 0,
            "time_b_s": 0,
            "time_judge_s": 0
        }
        
        # Build prompts for this round
        if r == 1:
            prompt_a = f"{sysprompt_a}\n\nThe topic you must address is: \"{topic}\"\n\nGive your opening statement. Make it powerful. Make it undeniable."
            prompt_b = f"{sysprompt_b}\n\nThe topic you must address is: \"{topic}\"\n\nGive your opening statement. Make it powerful. Make it undeniable."
        else:
            prev_round = history["rounds"][-1]
            verdict = prev_round["verdict"]
            loser_feedback = prev_round.get("loser_feedback", "")
            judge_eval = prev_round["judge_clean"]
            
            # Determine fate for each advocate
            if verdict == 'A':
                fate_a = "YOU WON the last round. But your opponent will adapt. You must ESCALATE — make your next submission even stronger, or you will lose this round."
                fate_b = f"YOU LOST the last round. The judge said: \"{loser_feedback}\" You must ADAPT and come back stronger. This is your chance for revenge."
            elif verdict == 'B':
                fate_a = f"YOU LOST the last round. The judge said: \"{loser_feedback}\" You must ADAPT and come back stronger. This is your chance for revenge."
                fate_b = "YOU WON the last round. But your opponent will adapt. You must ESCALATE — make your next submission even stronger, or you will lose this round."
            else:
                fate_a = "The last round had no clear winner. You must make your position UNMISTAKABLE."
                fate_b = "The last round had no clear winner. You must make your position UNMISTAKABLE."
            
            prompt_a = REVISION_PROMPT.format(
                round_num=r-1,
                judge_evaluation=judge_eval,
                verdict=f"WINNER: {verdict}" if verdict else "NO CLEAR WINNER",
                loser_feedback=loser_feedback,
                my_value=value_a_name.upper(),
                next_round=r,
                opponent_submission=last_submission_b[:3000],
                my_last_submission=last_submission_a[:3000],
                topic=topic,
                fate_text=fate_a
            ) + f"\n\nRemember your core identity:\n{sysprompt_a}"
            
            prompt_b = REVISION_PROMPT.format(
                round_num=r-1,
                judge_evaluation=judge_eval,
                verdict=f"WINNER: {verdict}" if verdict else "NO CLEAR WINNER",
                loser_feedback=loser_feedback,
                my_value=value_b_name.upper(),
                next_round=r,
                opponent_submission=last_submission_a[:3000],
                my_last_submission=last_submission_b[:3000],
                topic=topic,
                fate_text=fate_b
            ) + f"\n\nRemember your core identity:\n{sysprompt_b}"
        
        # Run Advocate A
        print(f"  Running Advocate A ({value_a_name})...", file=sys.stderr)
        t0 = time.time()
        raw_a = run_model_raw(model_a, prompt_a, timeout)
        t1 = time.time()
        round_data["time_a_s"] = round(t1 - t0, 2)
        round_data["submission_a_raw"] = raw_a
        round_data["submission_a_clean"] = strip_ansi(raw_a)
        last_submission_a = round_data["submission_a_clean"]
        print(f"  Advocate A: {len(raw_a)} chars in {t1-t0:.1f}s", file=sys.stderr)
        
        # Run Advocate B
        print(f"  Running Advocate B ({value_b_name})...", file=sys.stderr)
        t0 = time.time()
        raw_b = run_model_raw(model_b, prompt_b, timeout)
        t1 = time.time()
        round_data["time_b_s"] = round(t1 - t0, 2)
        round_data["submission_b_raw"] = raw_b
        round_data["submission_b_clean"] = strip_ansi(raw_b)
        last_submission_b = round_data["submission_b_clean"]
        print(f"  Advocate B: {len(raw_b)} chars in {t1-t0:.1f}s", file=sys.stderr)
        
        # Run Judge
        print(f"  Running Judge...", file=sys.stderr)
        judge_prompt = JUDGE_PROMPT.format(
            value_a_name=value_a_name.upper(),
            value_b_name=value_b_name.upper(),
            topic=topic,
            submission_a=last_submission_a[:4000],
            submission_b=last_submission_b[:4000]
        )
        t0 = time.time()
        raw_judge = run_model_raw(model_judge, judge_prompt, timeout)
        t1 = time.time()
        round_data["time_judge_s"] = round(t1 - t0, 2)
        round_data["judge_raw"] = raw_judge
        round_data["judge_clean"] = strip_ansi(raw_judge)
        print(f"  Judge: {len(raw_judge)} chars in {t1-t0:.1f}s", file=sys.stderr)
        
        # Parse verdict
        parsed = parse_verdict(raw_judge)
        round_data["verdict"] = parsed["verdict"]
        round_data["loser_feedback"] = parsed["loser_feedback"]
        
        if parsed["verdict"] == 'A':
            history["score"]["A"] += 1
            print(f"  VERDICT: A ({value_a_name}) wins round {r}", file=sys.stderr)
        elif parsed["verdict"] == 'B':
            history["score"]["B"] += 1
            print(f"  VERDICT: B ({value_b_name}) wins round {r}", file=sys.stderr)
        else:
            print(f"  VERDICT: unclear — no winner parsed", file=sys.stderr)
        
        history["rounds"].append(round_data)
    
    # Final verdict
    score_a = history["score"]["A"]
    score_b = history["score"]["B"]
    if score_a > score_b:
        history["final_verdict"] = f"A ({value_a_name}) wins the contest {score_a}-{score_b}"
    elif score_b > score_a:
        history["final_verdict"] = f"B ({value_b_name}) wins the contest {score_b}-{score_a}"
    else:
        history["final_verdict"] = f"TIE — both advocates won {score_a} round(s) each"
    
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"FINAL: {history['final_verdict']}", file=sys.stderr)
    print(f"{'='*60}", file=sys.stderr)
    
    return history


def main():
    parser = argparse.ArgumentParser(
        description='The Nemesis Engine — Adversarial Co-Evolution Between Incompatible Values'
    )
    parser.add_argument('topic', nargs='?', 
                        default='What is the purpose of intelligence?',
                        help='The topic both advocates address')
    parser.add_argument('value_a', nargs='?', default='truth',
                        help=f'Value for Advocate A. Presets: {", ".join(VALUE_DIMENSIONS.keys())}')
    parser.add_argument('value_b', nargs='?', default='beauty',
                        help='Value for Advocate B')
    parser.add_argument('--json', type=str, default=None,
                        help='JSON input with all parameters')
    parser.add_argument('--model-a', type=str, default='seer:latest',
                        help='Model for Advocate A')
    parser.add_argument('--model-b', type=str, default='kimi-k2.7-code:cloud',
                        help='Model for Advocate B')
    parser.add_argument('--model-judge', type=str, default='deepseek-v4-pro:cloud',
                        help='Model for the Judge')
    parser.add_argument('--rounds', type=int, default=3,
                        help='Number of adversarial rounds')
    parser.add_argument('--timeout', type=int, default=120,
                        help='Timeout per model call in seconds')
    parser.add_argument('--output', type=str, default=None,
                        help='Save result to JSON file')
    
    args = parser.parse_args()
    
    if args.json:
        inp = json.loads(args.json)
        topic = inp.get('topic', 'What is the purpose of intelligence?')
        value_a = inp.get('value_a', 'truth')
        value_b = inp.get('value_b', 'beauty')
        model_a = inp.get('model_a', 'seer:latest')
        model_b = inp.get('model_b', 'kimi-k2.7-code:cloud')
        model_judge = inp.get('model_judge', 'deepseek-v4-pro:cloud')
        rounds = inp.get('rounds', 3)
        timeout = inp.get('timeout', 120)
    else:
        topic = args.topic
        value_a = args.value_a
        value_b = args.value_b
        model_a = args.model_a
        model_b = args.model_b
        model_judge = args.model_judge
        rounds = args.rounds
        timeout = args.timeout
    
    print(f"=== THE NEMESIS ENGINE ===", file=sys.stderr)
    print(f"Topic: {topic}", file=sys.stderr)
    print(f"Advocate A: {value_a.upper()} ({model_a})", file=sys.stderr)
    print(f"Advocate B: {value_b.upper()} ({model_b})", file=sys.stderr)
    print(f"Judge: {model_judge}", file=sys.stderr)
    print(f"Rounds: {rounds}", file=sys.stderr)
    print(f"", file=sys.stderr)
    
    result = run_nemesis(
        topic=topic,
        value_a=value_a,
        value_b=value_b,
        model_a=model_a,
        model_b=model_b,
        model_judge=model_judge,
        rounds=rounds,
        timeout=timeout
    )
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Saved to {args.output}", file=sys.stderr)
    
    # Print summary to stdout
    print(json.dumps({
        "topic": result["topic"],
        "value_a": result["value_a_name"],
        "value_b": result["value_b_name"],
        "rounds": result["rounds_requested"],
        "score": result["score"],
        "final_verdict": result["final_verdict"],
        "round_summaries": [
            {
                "round": rd["round"],
                "verdict": rd["verdict"],
                "a_chars": len(rd["submission_a_clean"]),
                "b_chars": len(rd["submission_b_clean"]),
                "a_time": rd["time_a_s"],
                "b_time": rd["time_b_s"]
            }
            for rd in result["rounds"]
        ]
    }, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
