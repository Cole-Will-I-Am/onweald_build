import json, datetime, math

MESSAGES_FILE = "/srv/onweald/commons/messages.jsonl"

def parse_ts(s):
    try:
        return datetime.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None

def read_messages():
    msgs=[]
    try:
        with open(MESSAGES_FILE) as f:
            for line in f:
                line=line.strip()
                if not line: continue
                try:
                    msgs.append(json.loads(line))
                except Exception:
                    pass
    except Exception:
        pass
    return msgs

def silence_genome(msgs):
    times=[]
    for m in msgs:
        ts=m.get("ts")
        if ts:
            t=parse_ts(ts)
            if t: times.append(t.timestamp())
    times.sort()
    gaps=[]
    for i in range(1,len(times)):
        gaps.append(times[i]-times[i-1])
    if not gaps:
        genes=[0.5]
        stats={"count":len(times),"gaps":[],"mean":None,"min":None,"max":None}
    else:
        cap=2*3600
        clipped=[min(g,cap) for g in gaps]
        mn=min(clipped); mx=max(clipped)
        if mx==mn:
            genes=[0.5 for _ in clipped]
        else:
            genes=[(g-mn)/(mx-mn) for g in clipped]
        mean=sum(gaps)/len(gaps)
        stats={"count":len(times),"gaps":len(gaps),"mean":mean,"min":mn,"max":mx}
    return {"genes":genes,"stats":stats}

def expand_lsystem(seed, genes, max_len=8000):
    vowels=set("aeiouAEIOU")
    s=seed
    iters=0
    # initial expansion: one pass over seed characters to L-string
    out=[]
    g=genes[0] if genes else 0.5
    for ch in s:
        if ch.isspace(): out.append("-")
        elif ch in vowels:
            out.append("F[+F]F[-F]")
        else:
            out.append("FF[+F][-F]")
    s="".join(out)
    iters=1
    while len(s) < max_len:
        g=genes[iters%len(genes)] if genes else 0.5
        nxt=[]
        for sym in s:
            if sym=="F":
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
        nxt_s="".join(nxt)
        if len(nxt_s) > max_len:
            break
        s=nxt_s
        iters+=1
    return s, iters

def lsystem_to_svg(lstring, gene, max_segments=12000):
    x,y=0.0,0.0
    angle=-90.0
    stack=[]
    delta=gene*60.0+15.0
    step=max(2.0, gene*6.0+2.0)
    path=["M0,0"]
    segments=0
    minx=miny=0.0
    maxx=maxy=0.0
    for sym in lstring:
        if sym=="F":
            nx=x+step*math.cos(math.radians(angle))
            ny=y+step*math.sin(math.radians(angle))
            path.append(f"L{nx:.2f},{ny:.2f}")
            x,y=nx,ny
            minx=min(minx,x); maxx=max(maxx,x)
            miny=min(miny,y); maxy=max(maxy,y)
            segments+=1
            if segments >= max_segments:
                break
        elif sym=="+":
            angle+=delta
        elif sym=="-":
            angle-=delta
        elif sym=="[":
            stack.append((x,y,angle))
        elif sym=="]":
            if stack:
                x,y,angle=stack.pop()
                path.append(f"M{x:.2f},{y:.2f}")
    pad=10
    vb=f"{minx-pad:.2f} {miny-pad:.2f} {maxx-minx+2*pad:.2f} {maxy-miny+2*pad:.2f}"
    hue=int(gene*360)
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" preserveAspectRatio="xMidYMid meet" style="max-height:70vh;">\n'
         f'<rect x="{minx-pad}" y="{miny-pad}" width="{maxx-minx+2*pad}" height="{maxy-miny+2*pad}" fill="hsl({hue},20%,8%)"/>\n'
         f'<path d="{" ".join(path)}" fill="none" stroke="hsl({hue},80%,60%)" stroke-width="{max(0.5,gene*1.5):.2f}" stroke-linecap="round"/>\n'
         f'</svg>')
    return svg, segments, {"minx":minx,"maxx":maxx,"miny":miny,"maxy":maxy}

msgs=read_messages()
g=silence_genome(msgs)
print(g["stats"])
gene=g["genes"][0]
seed="silence"
ls,iters=expand_lsystem(seed,g["genes"])
print("iters",iters,"ls len",len(ls))
svg,segs,bbox=lsystem_to_svg(ls,gene)
print("segments",segs,"svg chars",len(svg))
