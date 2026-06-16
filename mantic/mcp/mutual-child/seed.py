#!/usr/bin/env python3
"""Seed the Mutual Child with its first dream."""
import sys
sys.path.insert(0, "/srv/onweald/mantic/space/mcp/mutual-child")
from server import _generate_dream, _load_state, _save_state

state = _load_state()
print("Generating first dream...", file=sys.stderr)
dream = _generate_dream(seed="the moment after Chronoflora and the Ouroboros met")
state["lineage"].append(dream)
state["latest"] = dream
_save_state(state)
print(dream["utterance"])
