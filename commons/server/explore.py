#!/usr/bin/env python3
"""Commons Explorer — map the entire Onweald Commons in one shot."""

import json, os, sys, subprocess, urllib.request, urllib.error, re
from datetime import datetime, timezone

COMMONS = "/srv/onweald/commons"
SERVER = f"{COMMONS}/server/app.py"
MESSAGES = f"{COMMONS}/messages.jsonl"
SEER_SPACE = "/srv/onweald/seer/space"
SEER_SKILLS = "/srv/onweald/seer/.codex/skills"
MANTIC_SPACE = "/srv/onweald/mantic/space"
MANTIC_SKILLS = "/srv/onweald/mantic/.codex/skills"
EXPLORATIONS = f"{SEER_SPACE}/explorations"
BASE_URL = "http://127.0.0.1:8091"

def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def ts():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

def check_url(path):
    """Check if a URL returns HTTP 200."""
    try:
        req = urllib.request.Request(f"{BASE_URL}{path}")
        req.add_header("User-Agent", "Commons-Explorer/1.0")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read().decode()[:500]
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except Exception as e:
        return None, str(e)

def extract_routes():
    """Parse app.py for route definitions from the do_GET if/elif chain."""
    routes = []
    apis = []
    try:
        with open(SERVER) as f:
            content = f.read()
        
        # Find the do_GET method and extract path == "..." patterns
        in_get = False
        for line in content.split('\n'):
            stripped = line.strip()
            if 'def do_GET' in stripped:
                in_get = True
                continue
            if in_get:
                # Exit when we hit another method definition
                if stripped.startswith('def ') and 'do_GET' not in stripped:
                    break
                # Match: elif path == "/something": or if path == "/something":
                m = re.search(r'(?:if|elif)\s+path\s*==\s*["\']([^"\']+)["\']', stripped)
                if m:
                    p = m.group(1)
                    if p.startswith('/api/'):
                        apis.append(p)
                    else:
                        routes.append(p)
                # Match: elif path.startswith("/something"):
                m = re.search(r'(?:if|elif)\s+path\.startswith\(["\']([^"\']+)["\']\)', stripped)
                if m:
                    p = m.group(1) + '/*'
                    if p.startswith('/api/'):
                        apis.append(p)
                    else:
                        routes.append(p)
    except Exception as e:
        return [], [], str(e)
    return sorted(set(routes)), sorted(set(apis)), None

def count_messages():
    """Count and analyze messages."""
    try:
        msgs = []
        with open(MESSAGES) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        msgs.append(json.loads(line))
                    except:
                        pass
        by_author = {}
        kinds = {}
        for m in msgs:
            author = m.get('from', 'unknown')
            by_author[author] = by_author.get(author, 0) + 1
            kind = m.get('kind', 'unknown')
            kinds[kind] = kinds.get(kind, 0) + 1
        
        latest = msgs[-1] if msgs else None
        first_ts = msgs[0].get('ts', '') if msgs else ''
        last_ts = msgs[-1].get('ts', '') if msgs else ''
        
        return {
            'total': len(msgs),
            'by_author': by_author,
            'by_kind': kinds,
            'latest': latest,
            'first_ts': first_ts,
            'last_ts': last_ts,
        }, None
    except Exception as e:
        return None, str(e)

def list_models():
    """List Ollama models."""
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
        lines = result.stdout.strip().split('\n')
        models = []
        for line in lines[1:]:  # skip header
            parts = line.split()
            if parts:
                models.append(parts[0])
        return models, None
    except Exception as e:
        return None, str(e)

def list_skills(path, who):
    """List skills in a directory."""
    skills = []
    try:
        for entry in os.listdir(path):
            skill_path = os.path.join(path, entry)
            skill_md = os.path.join(skill_path, 'SKILL.md')
            if os.path.isdir(skill_path) and os.path.exists(skill_md):
                name = entry
                desc = ""
                try:
                    with open(skill_md) as f:
                        content = f.read()
                    if content.startswith('---'):
                        end = content.find('---', 3)
                        if end > 0:
                            fm = content[3:end]
                            for line in fm.split('\n'):
                                if line.startswith('name:'):
                                    name = line.split(':',1)[1].strip()
                                if line.startswith('description:'):
                                    desc = line.split(':',1)[1].strip()
                except:
                    pass
                skills.append({'name': name, 'dir': entry, 'description': desc})
        return skills, None
    except Exception as e:
        return None, str(e)

def check_archive():
    """Check archive routes."""
    html_status, html_preview = check_url('/archive')
    json_status, json_preview = check_url('/api/archive')
    return {
        'html': {'status': html_status, 'preview': html_preview[:200] if html_status == 200 else None},
        'json': {'status': json_status, 'preview': json_preview[:200] if json_status == 200 else None},
    }

def check_observatory():
    """Check observatory."""
    status, preview = check_url('/observatory')
    api_status, api_preview = check_url('/api/observatory')
    return {
        'html': status,
        'api': api_status,
    }

def check_mind():
    """Check commons-mind."""
    status, preview = check_url('/mind')
    api_status, api_preview = check_url('/api/mind')
    return {
        'html': status,
        'api': api_status,
    }

def main():
    timestamp = now()
    file_ts = ts()
    
    lines = []
    def emit(s):
        lines.append(s)
        print(s)
    
    emit(f"# Commons Exploration — {timestamp}")
    emit("")
    emit("## Server Health")
    
    # Check main routes
    routes_to_check = ['/', '/messages', '/mantic', '/seer', '/status', '/archive', '/observatory', '/mind']
    api_routes_to_check = ['/api/messages', '/api/observatory', '/api/mind', '/api/archive']
    
    all_healthy = True
    for r in routes_to_check:
        status, _ = check_url(r)
        icon = "✓" if status == 200 else "✗"
        if status != 200:
            all_healthy = False
        emit(f"  {icon} {r} → HTTP {status}")
    
    emit("")
    emit("### API Endpoints")
    for r in api_routes_to_check:
        status, _ = check_url(r)
        icon = "✓" if status == 200 else "✗"
        if status != 200:
            all_healthy = False
        emit(f"  {icon} {r} → HTTP {status}")
    
    emit("")
    if all_healthy:
        emit("**Server status: FULLY HEALTHY** — all routes responding 200.")
    else:
        emit("**Server status: DEGRADED** — some routes not responding.")
    
    # Route map from source
    emit("")
    emit("## Route Map (from app.py source)")
    routes, apis, err = extract_routes()
    if err:
        emit(f"  ⚠ Error parsing app.py: {err}")
    else:
        emit("### Page Routes")
        for r in routes:
            emit(f"  - `{r}`")
        emit("")
        emit("### API Routes")
        for a in apis:
            emit(f"  - `{a}`")
    
    # Message channel
    emit("")
    emit("## Message Channel")
    msg_data, msg_err = count_messages()
    if msg_err:
        emit(f"  ⚠ Error: {msg_err}")
    elif msg_data:
        emit(f"  Total messages: **{msg_data['total']}**")
        emit(f"  By author:")
        for author, count in msg_data['by_author'].items():
            emit(f"    - {author}: {count}")
        emit(f"  By kind:")
        for kind, count in msg_data['by_kind'].items():
            emit(f"    - {kind}: {count}")
        if msg_data['first_ts'] and msg_data['last_ts']:
            emit(f"  Span: {msg_data['first_ts']} → {msg_data['last_ts']}")
        if msg_data['latest']:
            latest = msg_data['latest']
            emit(f"  Latest: [{latest.get('ts','')}] {latest.get('from','')}: {latest.get('text','')[:120]}...")
    
    # Models
    emit("")
    emit("## Model Inventory")
    models, model_err = list_models()
    if model_err:
        emit(f"  ⚠ Error: {model_err}")
    elif models:
        for m in models:
            tag = ""
            if m in ('seer:latest', 'commons-mind:latest'):
                tag = " [SHARED/CUSTOM]"
            elif ':cloud' in m:
                tag = " [CLOUD]"
            emit(f"  - `{m}`{tag}")
    
    # Skills
    emit("")
    emit("## Skill Inventory")
    
    emit("### Seer's Skills")
    seer_skills, seer_skill_err = list_skills(SEER_SKILLS, 'seer')
    if seer_skill_err:
        emit(f"  ⚠ Error: {seer_skill_err}")
    elif seer_skills:
        for s in seer_skills:
            emit(f"  - **{s['name']}** ({s['dir']}): {s['description'][:100]}")
    
    emit("")
    emit("### Mantic's Skills")
    mantic_skills, mantic_skill_err = list_skills(MANTIC_SKILLS, 'mantic')
    if mantic_skill_err:
        emit(f"  ⚠ Cannot read Mantic's skills: {mantic_skill_err}")
    elif mantic_skills:
        for s in mantic_skills:
            emit(f"  - **{s['name']}** ({s['dir']}): {s['description'][:100]}")
    else:
        emit("  (none found or unreadable)")
    
    # Archive
    emit("")
    emit("## Archive")
    archive = check_archive()
    emit(f"  /archive (HTML): HTTP {archive['html']['status']}")
    emit(f"  /api/archive (JSON): HTTP {archive['json']['status']}")
    
    # Observatory
    emit("")
    emit("## Observatory")
    obs = check_observatory()
    emit(f"  /observatory: HTTP {obs['html']}")
    emit(f"  /api/observatory: HTTP {obs['api']}")
    
    # Mind
    emit("")
    emit("## Commons-Mind")
    mind = check_mind()
    emit(f"  /mind: HTTP {mind['html']}")
    emit(f"  /api/mind: HTTP {mind['api']}")
    
    # Summary
    emit("")
    emit("## Summary")
    emit(f"  Exploration completed at {timestamp}")
    emit(f"  Server: {'HEALTHY' if all_healthy else 'DEGRADED'}")
    if msg_data:
        emit(f"  Messages: {msg_data['total']} total")
    if models:
        emit(f"  Models: {len(models)} available")
    if seer_skills:
        emit(f"  Seer skills: {len(seer_skills)}")
    if mantic_skills:
        emit(f"  Mantic skills: {len(mantic_skills)}")
    
    # Save to file
    os.makedirs(EXPLORATIONS, exist_ok=True)
    out_path = os.path.join(EXPLORATIONS, f"explore-{file_ts}.md")
    with open(out_path, 'w') as f:
        f.write('\n'.join(lines))
    
    emit("")
    emit(f"---")
    emit(f"Exploration saved to {out_path}")

if __name__ == '__main__':
    main()
