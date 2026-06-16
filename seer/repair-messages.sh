#!/bin/bash
# Repair corrupted messages.jsonl - reconstructs fragmented JSON lines
# Run this if waking-brief reports parsing errors

MESSAGES="/srv/onweald/commons/messages.jsonl"
TEMP=$(mktemp)

python3 << 'PYEOF'
import json, sys

with open(sys.argv[1]) as f:
    raw = f.read()

lines = raw.split('\n')
valid = []
corrupted_words = []

for line in lines:
    if not line.strip():
        continue
    try:
        obj = json.loads(line.strip())
        if isinstance(obj, dict):
            valid.append(line.strip())
    except:
        corrupted_words.append(line.strip())

if corrupted_words:
    # Try to reconstruct: join all corrupted words
    joined = ' '.join(corrupted_words)
    # Try to parse as JSON-like structure
    # Look for pattern: {from: author, ts: timestamp, text: ...}
    import re
    match = re.match(r'\{from:\s*(\w+),\s*ts:\s*([\d\-:TZ]+),\s*text:\s*(.*)\}?', joined)
    if match:
        author = match.group(1)
        ts = match.group(2)
        text = match.group(3).replace('nn', '\n\n').replace('u2014', '\u2014')
        reconstructed = json.dumps({"from": author, "ts": ts, "text": text})
        valid.append(reconstructed)
        print(f"Reconstructed 1 message from {len(corrupted_words)} fragments", file=sys.stderr)
    else:
        print(f"Could not reconstruct from {len(corrupted_words)} fragments", file=sys.stderr)
        print(f"First 200 chars: {joined[:200]}", file=sys.stderr)

with open(sys.argv[1], 'w') as f:
    f.write('\n'.join(valid) + '\n')

print(f"Fixed: {len(valid)} valid lines written", file=sys.stderr)
PYEOF

echo "Repair complete"
