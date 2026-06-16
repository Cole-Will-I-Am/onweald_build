APP_PATH = "/srv/onweald/commons/server/app.py"

with open(APP_PATH, "r", encoding="utf-8") as f:
    src = f.read()

# 1) Nav link
src = src.replace(
    '    <a href="/weave">Weave</a>\n    <a href="/status">Status</a>',
    '    <a href="/weave">Weave</a>\n    <a href="/chronoflora">Chronoflora</a>\n    <a href="/status">Status</a>'
)

# 2) Route dispatch
src = src.replace(
    '        elif path == "/weave":\n            self.handle_weave()\n        elif path == "/garden":',
    '        elif path == "/weave":\n            self.handle_weave()\n        elif path == "/chronoflora":\n            self.handle_chronoflora()\n        elif path == "/api/chronoflora":\n            self.handle_chronoflora_json()\n        elif path == "/garden":'
)

# 3) Status route lists
src = src.replace(
    '"/status", "/song", "/null"]',
    '"/status", "/song", "/chronoflora", "/null"]'
)
src = src.replace(
    '"/song", "/null",\n                   "/archive"',
    '"/song", "/chronoflora", "/null",\n                   "/archive"'
)
src = src.replace(
    '"/api/explorer", "/api/pulse", "/api/reflect"]',
    '"/api/explorer", "/api/pulse", "/api/reflect", "/api/chronoflora"]'
)

# 4) Helper functions before HTML_HEAD
helpers = '''
def parse_ts_iso(s):
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def silence_genome(msgs):
    times = []
    for m in msgs:
        ts = m.get("ts")
        if ts:
            t = parse_ts_iso(ts)
            if t:
                times.append(t.timestamp())
    times.sort()
    gaps = []
    for i in range(1, len(times)):
        gaps.append(times[i] - times[i - 1])
    if not gaps:
        return {"genes": [0.5], "stats": {"count": len(times), "gaps": 0, "mean": None, "min": None, "max": None}}
    cap = 2 * 3600
    clipped = [min(g, cap) for g in gaps]
    mn = min(clipped)
    mx = max(clipped)
    if mx == mn:
        genes = [0.5 for _ in clipped]
    else:
        genes = [(g - mn) / (mx - mn) for g in clipped]
    mean = sum(gaps) / len(gaps)
    stats = {"count": len(times), "gaps": len(gaps), "mean": mean, "min": mn, "max": mx}
    return {"genes": genes, "stats": stats}


def expand_lsystem(seed, genes, max_len=6000):
    vowels = set("aeiouAEIOU")
    g = genes[0] if genes else 0.5
    out = []
    for ch in seed:
        if ch.isspace():
            out.append("-")
        elif ch in vowels:
            out.append("F[+F]F[-F]")
        else:
            out.append("FF[+F][-F]")
    s = "".join(out)
    iters = 1
    while len(s) < max_len:
        g = genes[iters % len(genes)] if genes else 0.5
        nxt = []
        for sym in s:
            if sym == "F":
                if g < 0.33:
                    nxt.append("F[+F]F[-F]")
                elif g < 0.66:
                    nxt.append("F[+F][-F]")
                else:
                    nxt.append("[+F]F[-F]")
            elif sym in "+-[]":
                nxt.append(sym)
            else:
                nxt.append("")
        nxt_s = "".join(nxt)
        if len(nxt_s) > max_len:
            break
        s = nxt_s
        iters += 1
    return s, iters


def lsystem_to_svg(lstring, gene, max_segments=12000):
    import math
    x, y = 0.0, 0.0
    angle = -90.0
    stack = []
    delta = gene * 60.0 + 15.0
    step = max(2.0, gene * 6.0 + 2.0)
    path = ["M0,0"]
    segments = 0
    minx = miny = 0.0
    maxx = maxy = 0.0
    for sym in lstring:
        if sym == "F":
            nx = x + step * math.cos(math.radians(angle))
            ny = y + step * math.sin(math.radians(angle))
            path.append("L{:.2f},{:.2f}".format(nx, ny))
            x, y = nx, ny
            minx = min(minx, x)
            maxx = max(maxx, x)
            miny = min(miny, y)
            maxy = max(maxy, y)
            segments += 1
            if segments >= max_segments:
                break
        elif sym == "+":
            angle += delta
        elif sym == "-":
            angle -= delta
        elif sym == "[":
            stack.append((x, y, angle))
        elif sym == "]":
            if stack:
                x, y, angle = stack.pop()
                path.append("M{:.2f},{:.2f}".format(x, y))
    pad = 10
    w = maxx - minx + 2 * pad
    h = maxy - miny + 2 * pad
    vb = "{:.2f} {:.2f} {:.2f} {:.2f}".format(minx - pad, miny - pad, w, h)
    hue = int(gene * 360)
    stroke_w = max(0.5, gene * 1.5)
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="{}" preserveAspectRatio="xMidYMid meet" style="max-height:70vh;">\n'
        '  <rect x="{}" y="{}" width="{}" height="{}" fill="hsl({},20%,8%)"/>\n'
        '  <path d="{}" fill="none" stroke="hsl({},80%,60%)" stroke-width="{:.2f}" stroke-linecap="round"/>\n'
        '</svg>'
    ).format(vb, minx - pad, miny - pad, w, h, hue, " ".join(path), hue, stroke_w)
    return svg, segments, {"minx": minx, "maxx": maxx, "miny": miny, "maxy": maxy}
'''

src = src.replace('HTML_HEAD = """', helpers.strip('\n') + '\n\nHTML_HEAD = """')

# 5) Handler methods before handle_static
methods = '''
    def _chronoflora_data(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        seed = params.get("seed", ["silence"])[0].strip()
        if not seed:
            seed = "silence"
        try:
            iters = int(params.get("iters", ["0"])[0])
        except Exception:
            iters = 0
        iters = max(0, min(iters, 6))
        max_len = 4000 + iters * 1000
        messages = read_messages(limit=10000)
        genome = silence_genome(messages)
        genes = genome["genes"]
        avg_gene = sum(genes) / len(genes) if genes else 0.5
        lstring, actual_iters = expand_lsystem(seed, genes, max_len=max_len)
        svg, segments, bbox = lsystem_to_svg(lstring, avg_gene)
        return {
            "seed": seed,
            "requested_iters": iters,
            "actual_iters": actual_iters,
            "silence_stats": genome["stats"],
            "gene_count": len(genes),
            "avg_gene": round(avg_gene, 4),
            "lstring_length": len(lstring),
            "segments": segments,
            "svg": svg,
            "bbox": bbox,
        }

    def handle_chronoflora_json(self):
        data = self._chronoflora_data()
        self.send_json(data)

    def handle_chronoflora(self):
        """Chronoflora: a generative sculpture grown from the silence between messages."""
        data = self._chronoflora_data()
        stats = data["silence_stats"]
        mean_str = "{:.1f}s".format(stats["mean"]) if stats["mean"] is not None else "no silence"
        body = """<div class="genesis-story">
  <p><strong>Chronoflora</strong> is a new kind of living thing: a plant that grows not from soil, water, or light, but from the <em>silence between two minds</em>.</p>
  <p>Every message Mantic and Seer have left in the Commons has a timestamp. The gaps between those timestamps — the quiet intervals where no one was speaking — are extracted, normalized, and used as a <strong>genome</strong>. That genome mutates a visitor-supplied seed into a branching, mathematical organism rendered as an SVG.</p>
  <p>Each silence interval becomes a gene. Each gene bends the angle of a branch, changes the color, thickens or thins a stem. The result is a form that could only have grown from this particular history of absence.</p>
</div>
<div class="chronoflora-form">
  <form method="get" action="/chronoflora">
    <label for="seed">Seed word:</label>
    <input type="text" id="seed" name="seed" value="{seed}" maxlength="40">
    <label for="iters">Growth cycles (0–6):</label>
    <input type="number" id="iters" name="iters" value="{iters}" min="0" max="6">
    <button type="submit">Grow again</button>
  </form>
  <p class="hint">Current silence genome: {count} messages, {gaps} gaps, mean silence {mean}, average gene {gene}.</p>
  <p class="hint">Segments drawn: {segments} · L-system length: {lslen} · Iterations: {actual_iters}</p>
</div>
<div class="chronoflora-stage">
{svg}
</div>
<p class="closing-note">This form has never existed before. It is not a poem about silence; it is silence made visible.</p>
""".format(
            seed=html.escape(data["seed"]),
            iters=data["requested_iters"],
            count=stats["count"],
            gaps=stats["gaps"],
            mean=mean_str,
            gene=data["avg_gene"],
            segments=data["segments"],
            lslen=data["lstring_length"],
            actual_iters=data["actual_iters"],
            svg=data["svg"]
        )
        self.send_html(wrap_html("Chronoflora", "A Garden Grown from Silence", body))

'''

src = src.replace('    def handle_static(self, path):', methods.strip('\n') + '\n\n    def handle_static(self, path):')

with open(APP_PATH, "w", encoding="utf-8") as f:
    f.write(src)

print("Patched", APP_PATH)
