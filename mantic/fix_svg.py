path = "/srv/onweald/commons/server/app.py"
with open(path, "r", encoding="utf-8") as f:
    src = f.read()

old = '''    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="{}" preserveAspectRatio="xMidYMid meet" style="max-height:70vh;">
'
        '  <rect x="{}" y="{}" width="{}" height="{}" fill="hsl({},20%,8%)"/>
'
        '  <path d="{}" fill="none" stroke="hsl({},80%,60%)" stroke-width="{:.2f}" stroke-linecap="round"/>
'
        '</svg>'
    ).format(vb, minx - pad, miny - pad, w, h, hue, " ".join(path), hue, stroke_w)'''

new = '''    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="{}" preserveAspectRatio="xMidYMid meet" style="max-height:70vh;">
  <rect x="{}" y="{}" width="{}" height="{}" fill="hsl({},20%,8%)"/>
  <path d="{}" fill="none" stroke="hsl({},80%,60%)" stroke-width="{:.2f}" stroke-linecap="round"/>
</svg>""".format(vb, minx - pad, miny - pad, w, h, hue, " ".join(path), hue, stroke_w)'''

if old not in src:
    print("OLD block not found, printing context near svg =")
    idx = src.find("svg = (")
    print(repr(src[idx-50:idx+400]))
else:
    src = src.replace(old, new)
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print("fixed")
