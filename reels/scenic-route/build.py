"""Generate index.html for the scenic-route reel.

Run: python3 build.py   (then: npx hyperframes render)
All timing is computed here so the script, captions and stickers stay in sync.
"""
import html
import re
from pathlib import Path

W, H = 1080, 1920
TOTAL = 90.0
OUTRO = 3.2          # end lockup after the last caption
XFADE = 0.45         # scene crossfade

# Sticker kinds (x, y = top-left on the 1080x1920 canvas, r = rotation in degrees):
#   stamp(title, sub)      postage stamp          tag(title, sub, tone)  luggage tag
#   chip(text, tone)       little die-cut label   burst(text, tone)      starburst
#   note(text)             handwritten note       badge(title, sub)      round ribbon badge
#   hello(text)            "hello my name is"     shop(title, sub)       striped-awning shop sign
#   heart(text)            heart sticker          book(title, sub)       book cover
#   sign(text)             road sign w/ arrow     scribble()             crayon doodle
#   sparkles(points)       twinkling stars        arrow()                curly hand-drawn arrow
# "line": 1 makes a sticker wait for the scene's second sentence.
SCENES = [
    dict(bg="pirate", lines=["Nobody tells you your path can look like a *scribble* and still make sense."],
         stickers=[dict(k="note", text="my path:", x=90, y=190, r=-6),
                   dict(k="scribble", x=330, y=150, w=680, h=260, r=0),
                   dict(k="chip", text="still makes sense", tone="blush", x=560, y=430, r=4, line_word=10),
                   dict(k="sparkles", pts=[(60, 420), (1000, 170), (300, 480)])]),
    dict(bg="sweater", framed="tall", lines=["I grew up on *Long Island:* Bellmore, Sea Cliff, the North Shore."],
         stickers=[dict(k="stamp", title="Long Island", sub="greetings from", x=300, y=120, r=-4),
                   dict(k="chip", text="Bellmore", tone="teal", x=60, y=420, r=-7, line_word=5),
                   dict(k="chip", text="Sea Cliff", tone="blush", x=380, y=445, r=3, line_word=6),
                   dict(k="chip", text="North Shore", tone="paper", x=690, y=410, r=-4, line_word=9)]),
    dict(bg="pajamas", lines=["I was always the kid drawing *outside the lines.*"],
         stickers=[dict(k="box", x=250, y=200, w=580, h=230, r=-2),
                   dict(k="scribble", x=90, y=150, w=900, h=330, r=-3, color="pink", delay=0.6),
                   dict(k="note", text="(always)", x=720, y=440, r=8),
                   dict(k="sparkles", pts=[(120, 180), (980, 420)])]),
    dict(bg="profile", framed="tall", lines=["I started at community college and earned my *associate's.*"],
         stickers=[dict(k="badge", title="associate's", sub="earned it", x=370, y=150, r=-6, line_word=6),
                   dict(k="note", text="step one", x=120, y=230, r=-10),
                   dict(k="sparkles", pts=[(330, 170), (750, 200), (800, 470)])]),
    dict(bg="boardwalk", bg2="riverwalk", lines=["Then I moved to *Tampa* in 2015 to finish my bachelor's."],
         stickers=[dict(k="tag", title="Tampa", sub="est. 2015", tone="pink", x=330, y=170, r=-5),
                   dict(k="flight", x=60, y=430, w=960, h=170),
                   dict(k="chip", text="bachelor's era", tone="paper", x=610, y=480, r=5, line_word=8)]),
    dict(bg="icu", bg2="santa-hat", framed=True, lines=["Life had other plans, and that's *okay.*"],
         stickers=[dict(k="burst", text="plot twist!", tone="pink", x=300, y=130, r=-8),
                   dict(k="sparkles", pts=[(160, 220), (920, 180), (880, 520)])]),
    dict(bg="crepe-myrtle", framed=True, lines=["At 30 I moved to *Hilton Head* with my mom."],
         stickers=[dict(k="tag", title="Hilton Head", sub="age 30 + mom", tone="teal", x=230, y=170, r=4),
                   dict(k="sparkles", pts=[(140, 200), (960, 470)])]),
    dict(bg="wings", lines=["Starting over at 30 is *scary.* It's also kind of *magic.*"],
         stickers=[dict(k="burst", text="scary", tone="ink", x=60, y=180, r=-10, size=300, line_word=5),
                   dict(k="burst", text="magic", tone="blush", x=700, y=170, r=9, size=320, line_word=10),
                   dict(k="sparkles", pts=[(680, 200), (1010, 420), (640, 470), (980, 140)], line_word=10)]),
    dict(bg="beach-books", framed=True, lines=["Now I'm a graphic designer and children's book *author.*"],
         stickers=[dict(k="hello", text="designer + author", x=230, y=140, r=-4),
                   dict(k="sparkles", pts=[(160, 200), (930, 470)])]),
    dict(bg="draper", framed=True,
         lines=["I run *Court Creations:* websites and graphic design, plus my Etsy shop.",
                "This year is my *website journey.*"],
         stickers=[dict(k="shop", title="Court Creations", sub="websites + graphic design", x=160, y=110, r=-3),
                   dict(k="chip", text="+ Etsy shop", tone="blush", x=90, y=430, r=-6, line_word=10),
                   dict(k="chip", text="2026", tone="teal", x=640, y=440, r=4, line=1, line_word=4),
                   dict(k="sparkles", pts=[(120, 170), (980, 400)])]),
    dict(bg="nashville", framed=True,
         lines=["I founded Life Outside the Lines to make books where *every kid* sees themselves."],
         stickers=[dict(k="chip", text="Life Outside the Lines", tone="teal", x=150, y=170, r=-4),
                   dict(k="heart", text="every kid", x=650, y=250, r=8, line_word=10),
                   dict(k="note", text="founder!", x=170, y=330, r=-8)]),
    dict(bg="portrait", framed="tall", lines=["And I'm writing my memoir, *One in a Million.*"],
         stickers=[dict(k="book", title="One in a Million", sub="a memoir", x=90, y=150, r=-7, line_word=5),
                   dict(k="note", text="coming soon", x=520, y=260, r=6),
                   dict(k="arrow", x=560, y=330, w=240, h=170, r=0),
                   dict(k="sparkles", pts=[(470, 170), (1000, 210)])]),
    dict(bg="park", framed=True, lines=["So if your path looks messy right now, *keep going.*"],
         stickers=[dict(k="scribble", x=110, y=160, w=420, h=200, r=-4, color="cream"),
                   dict(k="sign", text="keep going", x=520, y=210, r=4, line_word=8)]),
    dict(bg="friends", lines=["The *scenic route* still gets you there."],
         stickers=[dict(k="sign", text="scenic route", x=230, y=170, r=-4),
                   dict(k="sparkles", pts=[(120, 190), (980, 220), (900, 520)])]),
]


def tokenize(sentence):
    """Split into words, tracking *emphasis* spans that may cover several words."""
    out, emph = [], False
    for raw in sentence.split():
        if raw.startswith("*"):
            emph = True
        out.append((raw.replace("*", ""), emph))
        if raw.endswith("*") or raw.rstrip(".,:;!?").endswith("*"):
            emph = False
    return out


def word_weight(word):
    w = 0.30 + 0.034 * len(word)
    if word.endswith((".", "!", "?")):
        w += 0.55
    elif word.endswith((",", ":", ";")):
        w += 0.22
    return w


# ---- timing -------------------------------------------------------------
SCENE_GAP = 0.35  # extra beat on every scene change
words = []        # dicts: text, emph, scene, line, t
t = 0.6
for si, sc in enumerate(SCENES):
    sc["raw_start"] = t - 0.6 if si == 0 else t - 0.25
    for li, line in enumerate(sc["lines"]):
        for word, emph in tokenize(line):
            words.append(dict(text=word, emph=emph, scene=si, line=(si, li), t=t))
            t += word_weight(word)
    t += SCENE_GAP
speech_end = t
scale = (TOTAL - OUTRO - 0.6) / (speech_end - 0.6)
for i, w in enumerate(words):
    w["t"] = round(0.6 + (w["t"] - 0.6) * scale, 3)
    w["id"] = f"w{i}"
for sc in SCENES:
    sc["start"] = round(0.6 + (sc["raw_start"] - 0.6) * scale, 3) if sc["raw_start"] > 0 else 0.0
for i, sc in enumerate(SCENES):
    nxt = SCENES[i + 1]["start"] if i + 1 < len(SCENES) else TOTAL
    sc["end"] = nxt + (XFADE if i + 1 < len(SCENES) else 0)
caption_end = TOTAL - OUTRO + 0.3


def word_time(si, line=0, n=0):
    """Absolute time of the n-th word of a scene's line."""
    ws = [w for w in words if w["line"] == (si, line)]
    return ws[min(n, len(ws) - 1)]["t"]


# ---- caption chunks: <= 4 words, break after punctuation or at a new sentence
chunks, cur = [], []
for i, w in enumerate(words):
    nxt = words[i + 1] if i + 1 < len(words) else None
    lone_tail = bool(re.search(r"[.,:;!?]$", w["text"])) or (nxt is None or nxt["line"] != w["line"])
    if cur and (cur[-1]["line"] != w["line"] or (len(cur) >= 4 and not (len(cur) == 4 and lone_tail))):
        chunks.append(cur)
        cur = []
    cur.append(w)
    if re.search(r"[.,:;!?]$", w["text"]):
        chunks.append(cur)
        cur = []
if cur:
    chunks.append(cur)
for i, ch in enumerate(chunks):
    ch_end = chunks[i + 1][0]["t"] if i + 1 < len(chunks) else caption_end
    chunks[i] = dict(words=ch, start=ch[0]["t"], end=ch_end)

# ---- stickers -----------------------------------------------------------
esc = html.escape
SPARK = "M12 0 C13 8 16 11 24 12 C16 13 13 16 12 24 C11 16 8 13 0 12 C8 11 11 8 12 0Z"


def burst_points(n=14, r1=50, r2=40):
    import math
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = math.pi * i / n - math.pi / 2
        pts.append(f"{50 + r * math.cos(a):.2f},{50 + r * math.sin(a):.2f}")
    return " ".join(pts)


BURST = burst_points()


def sticker(s, sid):
    """Return (html, kind of entrance) for one sticker."""
    k = s["k"]
    pos = f'left:{s.get("x", 0)}px; top:{s.get("y", 0)}px;'
    if k == "stamp":
        body = (f'<div class="stamp-in"><span class="stamp-sub">{esc(s["sub"])}</span>'
                f'<span class="stamp-title">{esc(s["title"])}</span><span class="stamp-ny">NY</span></div>')
        return f'<div class="stk stamp" id="{sid}" style="{pos}">{body}</div>'
    if k == "chip":
        return f'<div class="stk chip {s["tone"]}" id="{sid}" style="{pos}">{esc(s["text"])}</div>'
    if k == "tag":
        return (f'<div class="stk tag {s["tone"]}" id="{sid}" style="{pos}"><i class="hole"></i>'
                f'<span class="tag-title">{esc(s["title"])}</span><span class="tag-sub">{esc(s["sub"])}</span></div>')
    if k == "burst":
        size = s.get("size", 440)
        return (f'<div class="stk burst {s["tone"]}" id="{sid}" style="{pos} width:{size}px; height:{size}px;">'
                f'<svg viewBox="0 0 100 100"><polygon points="{BURST}"/></svg>'
                f'<span style="font-size:{size * 0.16:.0f}px">{esc(s["text"])}</span></div>')
    if k == "note":
        return f'<div class="stk note" id="{sid}" style="{pos}">{esc(s["text"])}</div>'
    if k == "badge":
        return (f'<div class="stk badge" id="{sid}" style="{pos}"><i class="ribbon l"></i><i class="ribbon r"></i>'
                f'<div class="badge-in"><span class="badge-star">&#9733;</span>'
                f'<span class="badge-title">{esc(s["title"])}</span><span class="badge-sub">{esc(s["sub"])}</span></div></div>')
    if k == "hello":
        return (f'<div class="stk hello" id="{sid}" style="{pos}"><div class="hello-top"><b>HELLO</b>'
                f'<span>my name is</span></div><div class="hello-body">{esc(s["text"])}</div></div>')
    if k == "shop":
        return (f'<div class="stk shop" id="{sid}" style="{pos}"><div class="awning"></div>'
                f'<div class="shop-body"><span class="shop-title">{esc(s["title"])}</span>'
                f'<span class="shop-sub">{esc(s["sub"])}</span></div></div>')
    if k == "heart":
        return (f'<div class="stk heart" id="{sid}" style="{pos}"><svg viewBox="0 0 100 92">'
                f'<path d="M50 90 C 20 66, 0 48, 0 26 C 0 10, 12 0, 27 0 C 38 0, 46 6, 50 15 '
                f'C 54 6, 62 0, 73 0 C 88 0, 100 10, 100 26 C 100 48, 80 66, 50 90Z"/></svg>'
                f'<span>{esc(s["text"])}</span></div>')
    if k == "book":
        return (f'<div class="stk book" id="{sid}" style="{pos}"><div class="spine"></div>'
                f'<span class="book-title">{esc(s["title"])}</span><span class="book-rule"></span>'
                f'<span class="book-sub">{esc(s["sub"])}</span></div>')
    if k == "sign":
        return (f'<div class="stk sign" id="{sid}" style="{pos}"><span>{esc(s["text"])}</span>'
                f'<svg viewBox="0 0 60 40"><path d="M4 20 H50 M36 6 L52 20 L36 34"/></svg></div>')
    if k == "box":
        return (f'<div class="stk box" id="{sid}" style="{pos} width:{s["w"]}px; height:{s["h"]}px;">'
                f'<span>the lines</span></div>')
    if k in ("scribble", "flight", "arrow"):
        paths = {
            "scribble": "M10 160 C 60 20, 120 260, 180 120 S 260 10, 300 150 S 380 260, 420 90 "
                        "S 500 10, 540 170 S 620 250, 660 80 S 760 60, 790 150",
            "flight": "M10 140 C 160 20, 280 170, 420 90 S 640 10, 760 110 S 900 60, 950 40",
            "arrow": "M20 20 C 120 0, 200 40, 170 100 C 150 140, 90 120, 110 90 C 130 60, 200 110, 220 160",
        }
        vb = {"scribble": "0 0 800 270", "flight": "0 0 960 170", "arrow": "0 0 240 170"}[k]
        color = s.get("color", "blush")
        extra = ""
        if k == "flight":
            extra = (f'<g class="plane" id="{sid}-plane"><path d="M0 -10 L26 0 L0 10 L6 0Z"/></g>')
        if k == "arrow":
            extra = '<path class="head" d="M200 150 L222 162 L226 138"/>'
        return (f'<div class="stk doodle {k} {color}" id="{sid}" style="{pos} width:{s["w"]}px; height:{s["h"]}px;">'
                f'<svg viewBox="{vb}" preserveAspectRatio="none"><path class="ink" id="{sid}-path" '
                f'pathLength="1" d="{paths[k]}"/>{extra}</svg></div>')
    if k == "sparkles":
        return "".join(
            f'<svg class="spark" id="{sid}-{n}" style="left:{x}px; top:{y}px;" viewBox="0 0 24 24">'
            f'<path d="{SPARK}"/></svg>' for n, (x, y) in enumerate(s["pts"]))
    raise ValueError(k)


sections, js = [], []
for si, sc in enumerate(SCENES):
    dur = round(sc["end"] - sc["start"], 3)
    st = sc["start"]
    bgs = [sc["bg"]] + ([sc["bg2"]] if sc.get("bg2") else [])
    if sc.get("framed"):
        tall = sc["framed"] == "tall"
        media = (f'<img class="bg" id="s{si}-bg" src="assets/media/{sc["bg"]}-bg.jpg" alt="">'
                 f'<div class="photo{" tall" if tall else ""}" id="s{si}-photo">'
                 f'<img src="assets/media/{sc["bg"]}.jpg" alt="">'
                 + (f'<img class="ph2" id="s{si}-ph2" src="assets/media/{sc["bg2"]}.jpg" alt="">' if sc.get("bg2") else "")
                 + '<i class="tape"></i></div>')
        if sc.get("bg2"):
            media = (f'<img class="bg" id="s{si}-bgb" src="assets/media/{sc["bg2"]}-bg.jpg" alt="">' + media)
            media = media.replace(f'<img class="bg" id="s{si}-bg" ', f'<img class="bg" id="s{si}-bg" style="z-index:0" ', 1)
    else:
        media = "".join(
            f'<img class="bg" id="s{si}-bg{j}" src="assets/media/{b}.jpg" alt="">' for j, b in enumerate(bgs))
    stk_html = "".join(sticker(s, f"s{si}-k{n}") for n, s in enumerate(sc["stickers"]))
    sections.append(f'''
      <section class="clip scene" id="s{si}" data-start="{st}" data-duration="{dur}" data-track-index="1">
        <div class="inner" id="s{si}-inner">
          {media}
          <div class="shade"></div>
          <div class="stickers" id="s{si}-stk">{stk_html}</div>
        </div>
      </section>''')

    # scene motion (times are absolute on the root timeline)
    if si > 0:
        js.append(f'tl.fromTo("#s{si}-inner", {{opacity: 0}}, {{opacity: 1, duration: {XFADE}, ease: "power1.inOut"}}, {st});')
    if sc.get("framed"):
        js.append(f'tl.fromTo("#s{si}-photo", {{y: 24, rotation: -3}}, {{y: 0, rotation: -1.2, duration: 0.6, ease: "power2.out"}}, {st});')
        js.append(f'tl.fromTo("#s{si}-photo img", {{scale: 1}}, {{scale: 1.05, duration: {dur}, ease: "none"}}, {st});')
        if sc.get("bg2"):
            half = round(st + dur / 2, 3)
            js.append(f'tl.fromTo("#s{si}-ph2", {{opacity: 0}}, {{opacity: 1, duration: 0.5, ease: "power1.inOut"}}, {half});')
            js.append(f'tl.fromTo("#s{si}-bg", {{opacity: 1}}, {{opacity: 0, duration: 0.5, ease: "power1.inOut"}}, {half});')
    elif len(bgs) == 2:
        half = round(dur / 2, 3)
        js.append(f'tl.fromTo("#s{si}-bg0", {{scale: 1.0}}, {{scale: 1.05, duration: {dur}, ease: "none"}}, {st});')
        js.append(f'tl.fromTo("#s{si}-bg1", {{opacity: 0, scale: 1.0}}, {{opacity: 1, scale: 1.03, duration: 0.5, ease: "power1.inOut"}}, {st + half});')
    else:
        js.append(f'tl.fromTo("#s{si}-bg0", {{scale: 1.0}}, {{scale: 1.06, duration: {dur}, ease: "none"}}, {st});')

    for n, s in enumerate(sc["stickers"]):
        sid = f"s{si}-k{n}"
        line = s.get("line", 0)
        if "line_word" in s or line:
            at = word_time(si, line, s.get("line_word", 0))
        else:
            at = st + 0.3 + n * 0.35
        at += s.get("delay", 0)
        r = s.get("r", 0)
        k = s["k"]
        if k == "sparkles":
            for p in range(len(s["pts"])):
                pt = at + p * 0.15
                js.append(f'tl.fromTo("#{sid}-{p}", {{opacity: 0, scale: 0}}, {{opacity: 1, scale: 1, duration: 0.3, ease: "power2.out"}}, {pt:.3f});')
                # gentle twinkle, finite
                js.append(f'tl.to("#{sid}-{p}", {{scale: 0.6, rotation: 45, duration: 0.6, ease: "sine.inOut", yoyo: true, repeat: 3}}, {pt + 0.4:.3f});')
        elif k in ("scribble", "flight", "arrow"):
            js.append(f'tl.fromTo("#{sid}", {{opacity: 0, rotation: {r}}}, {{opacity: 1, rotation: {r}, duration: 0.1}}, {at:.3f});')
            js.append(f'tl.fromTo("#{sid}-path", {{strokeDashoffset: 1}}, {{strokeDashoffset: 0, duration: 1.1, ease: "power1.inOut"}}, {at:.3f});')
            if k == "flight":
                js.append(f'tl.fromTo("#{sid}-plane", {{opacity: 0}}, {{opacity: 1, duration: 0.2}}, {at + 0.9:.3f});')
        else:
            # sticker slap: lands from slightly bigger with a twist
            js.append(f'tl.fromTo("#{sid}", {{opacity: 0, scale: 1.35, rotation: {r - 10}}}, '
                      f'{{opacity: 1, scale: 1, rotation: {r}, duration: 0.3, ease: "power3.out"}}, {at:.3f});')
    if si < len(SCENES) - 1:
        js.append(f'tl.to("#s{si}-stk", {{opacity: 0, duration: 0.25, ease: "power1.in"}}, {sc["end"] - XFADE - 0.15:.3f});')
    else:
        js.append(f'tl.to("#s{si}-stk", {{opacity: 0, duration: 0.3, ease: "power1.in"}}, {caption_end - 0.3:.3f});')

cap_html = []
for ci, ch in enumerate(chunks):
    spans, group, gwords = [], [], []

    def flush():
        if group:
            gid = "g" + gwords[0]["id"]
            spans.append(f'<span class="emg" id="{gid}">' + " ".join(group) + "</span>")
            js.append(f'tl.fromTo("#{gid}", {{opacity: 0, scaleX: 0.6}}, {{opacity: 1, scaleX: 1, duration: 0.16, ease: "power3.out"}}, {gwords[0]["t"]});')
            group.clear()
            gwords.clear()
    for w in ch["words"]:
        span = f'<span class="{"w em" if w["emph"] else "w"}" id="{w["id"]}">{esc(w["text"])}</span>'
        if w["emph"]:
            group.append(span)
            gwords.append(w)
        else:
            flush()
            spans.append(span)
    flush()
    for w in ch["words"]:
        if w["emph"]:
            js.append(f'tl.fromTo("#{w["id"]}", {{opacity: 0, scale: 1.25}}, {{opacity: 1, scale: 1, duration: 0.18, ease: "power3.out"}}, {w["t"]});')
        else:
            js.append(f'tl.fromTo("#{w["id"]}", {{opacity: 0, y: 6}}, {{opacity: 1, y: 0, duration: 0.14, ease: "power2.out"}}, {w["t"]});')
    cap_html.append(f'<div class="chunk" id="c{ci}">{" ".join(spans)}</div>')
    js.append(f'tl.set("#c{ci}", {{opacity: 1}}, {ch["start"]});')
    js.append(f'tl.set("#c{ci}", {{opacity: 0}}, {ch["end"]});')

outro_t = caption_end + 0.1
js.append(f'tl.fromTo("#outro-sig", {{opacity: 0, scale: 1.2, rotation: -12}}, {{opacity: 1, scale: 1, rotation: -6, duration: 0.36, ease: "power3.out"}}, {outro_t:.3f});')
js.append(f'tl.fromTo("#outro-handle", {{opacity: 0, rotation: 6}}, {{opacity: 1, rotation: 3, duration: 0.3}}, {outro_t + 0.35:.3f});')

fonts = "\n".join(
    f'@font-face {{ font-family: "{fam}"; src: url("assets/fonts/{f}.woff2") format("woff2"); '
    f'font-weight: {wt}; font-style: {style}; }}'
    for fam, f, wt, style in [
        ("Gelasio", "gelasio-latin-400-normal", 400, "normal"),
        ("Gelasio", "gelasio-latin-400-italic", 400, "italic"),
        ("Gelasio", "gelasio-latin-700-normal", 700, "normal"),
        ("Gelasio", "gelasio-latin-700-italic", 700, "italic"),
        ("Caveat", "caveat-latin-700-normal", 700, "normal"),
        ("Parisienne", "parisienne-latin-400-normal", 400, "normal"),
    ])

doc = f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={W}, height={H}" />
    <title>The scenic route</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
{fonts}
:root {{
  --ink: #221F1E; --paper: #FFFDF7; --cream: #FBF7EE; --sand: #E6DCCD;
  --blush: #F9B9D2; --pink: #EE3B84; --pink-600: #D62769; --teal-200: #A6E3DB; --teal: #1E9A99;
  --teal-600: #0F7C7C; --mint: #A8DCC4;
}}
body {{ margin: 0; background: var(--ink); }}
#root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: var(--ink);
  font-family: "Gelasio", Georgia, serif; }}
.scene {{ position: absolute; inset: 0; }}
.inner {{ position: absolute; inset: 0; overflow: hidden; }}
.bg {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transform-origin: 50% 40%; }}
.photo {{ position: absolute; left: 200px; top: 560px; width: 680px; height: 907px; padding: 18px;
  background: var(--paper); border-radius: 8px; box-sizing: border-box;
  box-shadow: 0 24px 60px rgba(70, 52, 30, 0.35), 0 4px 12px rgba(70, 52, 30, 0.25); }}
.photo.tall {{ left: 230px; width: 620px; height: 1102px; }}
.photo .ph2 {{ position: absolute; left: 18px; top: 18px; width: calc(100% - 36px); height: calc(100% - 36px); }}
.photo img {{ display: block; width: 100%; height: 100%; object-fit: cover; border-radius: 3px; }}
.tape {{ position: absolute; left: 50%; top: -26px; width: 220px; height: 56px; margin-left: -110px;
  background: rgba(168, 220, 196, 0.78); transform: rotate(-4deg);
  clip-path: polygon(2% 0, 98% 4%, 100% 50%, 97% 100%, 3% 96%, 0 50%); }}
.shade {{ position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(20,16,15,0.35) 0%, rgba(20,16,15,0) 30%,
    rgba(20,16,15,0) 58%, rgba(20,16,15,0.55) 78%, rgba(20,16,15,0.72) 100%); }}
.stickers {{ position: absolute; inset: 0; }}
.stk {{ position: absolute; }}
/* die-cut sticker edge: white outline + soft drop */
.stamp, .chip, .tag, .badge, .hello, .shop, .book, .sign {{
  filter: drop-shadow(0 0 0 #fff) drop-shadow(0 10px 18px rgba(20,16,15,0.35)); }}
.chip {{ padding: 10px 26px 12px; border-radius: 999px; font-size: 44px; font-weight: 700; font-style: italic;
  border: 6px solid #fff; white-space: nowrap; }}
.chip.blush {{ background: var(--blush); color: var(--ink); }}
.chip.teal {{ background: var(--teal-600); color: #fff; }}
.chip.paper {{ background: var(--paper); color: var(--ink); }}
.stamp {{ width: 480px; padding: 16px; background: var(--paper); border-radius: 6px;
  outline: 8px dotted var(--paper); outline-offset: -2px; }}
.stamp-in {{ border: 4px dashed var(--pink); border-radius: 6px; padding: 26px 20px 30px; display: flex;
  flex-direction: column; align-items: center; background: #FFF1F6; position: relative; }}
.stamp-sub {{ font-family: "Caveat", cursive; font-size: 46px; color: var(--teal-600); line-height: 1; }}
.stamp-title {{ font-size: 76px; font-weight: 700; font-style: italic; color: var(--pink-600); line-height: 1.05; }}
.stamp-ny {{ position: absolute; right: 14px; top: 10px; font-size: 26px; font-weight: 700; color: var(--teal-600); }}
.tag {{ display: flex; flex-direction: column; align-items: flex-start; padding: 22px 46px 26px 90px;
  border-radius: 18px; color: #fff; clip-path: polygon(40px 0, 100% 0, 100% 100%, 40px 100%, 0 50%); }}
.tag.pink {{ background: var(--pink-600); }}
.tag.teal {{ background: var(--teal-600); }}
.tag .hole {{ position: absolute; left: 36px; top: 50%; width: 22px; height: 22px; margin-top: -11px;
  border-radius: 50%; background: var(--paper); }}
.tag-title {{ font-size: 88px; font-weight: 700; font-style: italic; line-height: 1; white-space: nowrap; }}
.tag-sub {{ font-family: "Caveat", cursive; font-size: 46px; line-height: 1.1; color: var(--blush); }}
.tag.teal .tag-sub {{ color: var(--teal-200); }}
.burst {{ display: grid; place-items: center; }}
.burst svg {{ position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible;
  filter: drop-shadow(0 10px 18px rgba(20,16,15,0.35)); }}
.burst polygon {{ stroke: #fff; stroke-width: 2.4; stroke-linejoin: round; }}
.burst.pink polygon {{ fill: var(--pink-600); }}
.burst.blush polygon {{ fill: var(--blush); }}
.burst.ink polygon {{ fill: var(--ink); }}
.burst span {{ position: relative; font-weight: 700; font-style: italic; color: #fff; white-space: nowrap; }}
.burst.blush span {{ color: var(--ink); }}
.note {{ font-family: "Caveat", cursive; font-size: 78px; color: #fff; white-space: nowrap;
  text-shadow: 0 3px 14px rgba(20,16,15,0.7); }}
.badge {{ width: 330px; height: 330px; }}
.badge-in {{ position: absolute; inset: 0; border-radius: 50%; background: var(--blush); border: 8px solid #fff;
  display: flex; flex-direction: column; align-items: center; justify-content: center; box-sizing: border-box;
  box-shadow: inset 0 0 0 10px var(--blush), inset 0 0 0 14px var(--pink); }}
.badge-star {{ font-size: 56px; color: var(--pink-600); line-height: 1; }}
.badge-title {{ font-size: 52px; font-weight: 700; font-style: italic; color: var(--ink); line-height: 1.1; }}
.badge-sub {{ font-family: "Caveat", cursive; font-size: 44px; color: var(--pink-600); }}
.ribbon {{ position: absolute; bottom: -70px; width: 70px; height: 140px; background: var(--pink-600);
  clip-path: polygon(0 0, 100% 0, 100% 100%, 50% 80%, 0 100%); }}
.ribbon.l {{ left: 90px; transform: rotate(18deg); }}
.ribbon.r {{ right: 90px; transform: rotate(-18deg); }}
.hello {{ width: 620px; border-radius: 26px; overflow: hidden; background: var(--pink-600); border: 6px solid #fff; }}
.hello-top {{ display: flex; flex-direction: column; align-items: center; padding: 14px 0 10px; color: #fff; }}
.hello-top b {{ font-size: 72px; letter-spacing: 0.08em; line-height: 1; }}
.hello-top span {{ font-size: 34px; font-style: italic; }}
.hello-body {{ margin: 0 22px 22px; padding: 22px 10px 26px; background: var(--paper); border-radius: 10px;
  text-align: center; font-family: "Caveat", cursive; font-size: 84px; color: var(--ink); line-height: 1; }}
.shop {{ width: 760px; }}
.awning {{ height: 70px; border-radius: 14px 14px 0 0; border: 6px solid #fff; border-bottom: 0;
  background: repeating-linear-gradient(90deg, var(--pink) 0 60px, var(--paper) 60px 120px);
  -webkit-mask: radial-gradient(circle 30px at 30px 100%, transparent 98%, #000) 0 0 / 60px 100%; }}
.shop-body {{ display: flex; flex-direction: column; align-items: center; padding: 18px 20px 24px;
  background: var(--paper); border: 6px solid #fff; border-top: 0; border-radius: 0 0 16px 16px; }}
.shop-title {{ font-size: 72px; white-space: nowrap; font-weight: 700; font-style: italic; color: var(--pink-600); line-height: 1.05; }}
.shop-sub {{ font-family: "Caveat", cursive; font-size: 54px; color: var(--teal-600); }}
.heart {{ width: 330px; height: 304px; display: grid; place-items: center; }}
.heart svg {{ position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible;
  filter: drop-shadow(0 10px 18px rgba(20,16,15,0.35)); }}
.heart path {{ fill: var(--pink-600); stroke: #fff; stroke-width: 4; }}
.heart span {{ position: relative; margin-top: -30px; font-size: 54px; font-weight: 700; font-style: italic;
  color: #fff; white-space: nowrap; }}
.book {{ width: 330px; height: 440px; border-radius: 6px 16px 16px 6px; background: var(--teal-600);
  border: 6px solid #fff; display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 0 30px 0 50px; box-sizing: border-box; text-align: center; }}
.spine {{ position: absolute; left: 0; top: 0; bottom: 0; width: 26px; background: rgba(20,16,15,0.25); }}
.book-title {{ font-size: 62px; font-weight: 700; font-style: italic; color: #fff; line-height: 1.05; }}
.book-rule {{ width: 90px; height: 4px; margin: 20px 0 14px; background: var(--blush); }}
.book-sub {{ font-family: "Caveat", cursive; font-size: 48px; color: var(--blush); }}
.sign {{ display: flex; align-items: center; gap: 18px; padding: 20px 34px 24px; border-radius: 18px;
  background: var(--teal-600); color: #fff; border: 6px solid #fff;
  box-shadow: inset 0 0 0 6px var(--teal-600), inset 0 0 0 9px rgba(255,255,255,0.7); }}
.sign span {{ font-size: 74px; font-weight: 700; font-style: italic; white-space: nowrap; }}
.sign svg {{ width: 84px; height: 56px; fill: none; stroke: #fff; stroke-width: 6; stroke-linecap: round;
  stroke-linejoin: round; }}
.box {{ border: 6px dashed rgba(255,255,255,0.85); border-radius: 14px; }}
.box span {{ position: absolute; left: 18px; top: -58px; font-family: "Caveat", cursive; font-size: 50px;
  color: #fff; text-shadow: 0 2px 10px rgba(20,16,15,0.7); }}
.doodle svg {{ width: 100%; height: 100%; overflow: visible; }}
.doodle .ink {{ fill: none; stroke-width: 14; stroke-linecap: round; stroke-linejoin: round;
  stroke-dasharray: 1; vector-effect: non-scaling-stroke; filter: drop-shadow(0 4px 8px rgba(20,16,15,0.45)); }}
.doodle.blush .ink {{ stroke: var(--blush); }}
.doodle.pink .ink {{ stroke: var(--pink); }}
.doodle.cream .ink {{ stroke: var(--cream); }}
.doodle.flight .ink {{ stroke-width: 7; stroke: #fff; }}
.doodle .head {{ fill: none; stroke: var(--blush); stroke-width: 14; stroke-linecap: round; stroke-linejoin: round;
  vector-effect: non-scaling-stroke; }}
.plane {{ transform: translate(950px, 40px) rotate(-14deg); }}
.plane path {{ fill: #fff; }}
.spark {{ position: absolute; width: 60px; height: 60px; overflow: visible; }}
.spark path {{ fill: #fff; filter: drop-shadow(0 0 10px rgba(249,185,210,0.9)); }}
.captions {{ position: absolute; left: 60px; right: 60px; bottom: 420px; height: 280px; }}
.chunk {{ position: absolute; inset: 0; display: flex; flex-wrap: wrap; align-content: flex-end;
  justify-content: center; column-gap: 20px; row-gap: 6px; opacity: 0; text-align: center; }}
.w {{ display: inline-block; color: #FFFFFF; font-weight: 700; font-size: 86px; line-height: 1.12;
  text-shadow: 0 3px 0 rgba(34,31,30,0.55), 0 6px 22px rgba(20,16,15,0.75); }}
.emg {{ display: inline-flex; flex-wrap: wrap; justify-content: center; column-gap: 18px; padding: 0 20px 6px;
  background: var(--blush); border-radius: 14px; box-shadow: 0 6px 18px rgba(20,16,15,0.35); }}
.w.em {{ color: var(--ink); font-style: italic; text-shadow: none; }}
.outro {{ position: absolute; left: 0; right: 0; bottom: 330px; display: flex; flex-direction: column;
  align-items: center; gap: 22px; }}
#outro-sig {{ font-family: "Parisienne", cursive; font-size: 150px; color: var(--blush); line-height: 1;
  text-shadow: 0 4px 22px rgba(20,16,15,0.75); }}
#outro-handle {{ padding: 10px 28px 12px; border-radius: 999px; background: var(--paper); color: var(--pink-600);
  border: 6px solid #fff; font-size: 40px; font-weight: 700; font-style: italic;
  box-shadow: 0 10px 18px rgba(20,16,15,0.35); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="{W}" data-height="{H}"
         data-duration="{TOTAL}" data-fps="30">
{"".join(sections)}
      <div class="clip captions" id="captions" data-start="0" data-duration="{TOTAL}" data-track-index="2">
        {"".join(cap_html)}
      </div>
      <div class="clip outro" id="outro" data-start="{round(caption_end, 3)}" data-duration="{round(TOTAL - caption_end, 3)}" data-track-index="3">
        <div id="outro-sig">xo, court</div>
        <div id="outro-handle">@courtcreations94</div>
      </div>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {chr(10).join("      " + l for l in js).lstrip()}
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
'''
Path(__file__).with_name("index.html").write_text(doc)
print(f"{len(words)} words, {len(chunks)} caption chunks, speech ends {caption_end:.1f}s")
