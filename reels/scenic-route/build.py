"""Generate index.html for the scenic-route reel.

Run: python3 build.py   (then: npx hyperframes render)
All timing is computed here so the script, captions and cards stay in sync.
"""
import html
import re
from pathlib import Path

W, H = 1080, 1920
TOTAL = 90.0
OUTRO = 3.2          # end lockup after the last caption
XFADE = 0.45         # scene crossfade

# Each scene: background, sentences (with *emphasis*), header pill, terminal card.
# Card lines: ("k", key, value) key/value, ("t", text) plain, ("ok", text) checked,
# ("meter", label, pct), ("cmd", text) prompt line, ("scribble",) animated doodle.
SCENES = [
    dict(bg="pirate", lines=["Nobody tells you your path can look like a *scribble* and still make sense."],
         pill="Nobody tells you <em>this</em>", file="trace --path court",
         card=[("cmd", "trace --path court"), ("k", "shape", "scribble"), ("ok", "still makes sense")]),
    dict(bg="sweater", lines=["I grew up on *Long Island:* Bellmore, Sea Cliff, the North Shore."],
         pill="Where it <em>started</em>", file="origin.json",
         card=[("k", "home", "Long Island, NY"), ("k", "towns", "Bellmore · Sea Cliff"), ("k", "", "North Shore")]),
    dict(bg="pajamas", lines=["I was always the kid drawing *outside the lines.*"],
         pill="The kid outside the <em>lines</em>", file="draw.js",
         card=[("cmd", "draw({ lines: false })"), ("scribble",)]),
    dict(bg="profile", framed="tall", lines=["I started at community college and earned my *associate's.*"],
         pill="Step <em>one</em>", file="education.log",
         card=[("t", "community college"), ("meter", "associate's", 100), ("ok", "earned")]),
    dict(bg="boardwalk", bg2="riverwalk", lines=["Then I moved to *Tampa* in 2015 to finish my bachelor's."],
         pill="Tampa, <em>2015</em>", file="route.map",
         card=[("route", "LI", "TPA"), ("k", "goal", "bachelor's"), ("t", "loading next chapter…")]),
    dict(bg="sunset-palm", lines=["Life had other plans, and that's *okay.*"],
         pill="Plot <em>twist</em>", file="plan_a.exe",
         card=[("err", "life had other plans"), ("cmd", "reroute"), ("ok", "that's okay")]),
    dict(bg="wings", lines=["At 30 I moved to *Hilton Head* with my mom.",
                            "Starting over at 30 is *scary.* It's also kind of *magic.*"],
         pill="Starting over at <em>30</em>", file="restart.sh",
         card=[("route", "TPA", "HHI"), ("meter", "scary", 82), ("meter", "magic", 100)]),
    dict(bg="beanie", lines=["Now I'm a graphic designer and children's book *author.*"],
         pill="Now", file="whoami",
         card=[("cmd", "whoami"), ("ok", "graphic designer"), ("ok", "children's book author")]),
    dict(bg="draper", framed=True, lines=["I run *Court Creations* on Etsy."],
         pill="Court <em>Creations</em>", file="shop.status",
         card=[("k", "shop", "Court Creations"), ("k", "on", "Etsy"), ("ok", "open")]),
    dict(bg="nashville", framed=True,
         lines=["I founded Life Outside the Lines to make books where *every kid* sees themselves."],
         pill="Life Outside the <em>Lines</em>", file="mission.md",
         card=[("k", "founded", "Life Outside the Lines"), ("k", "makes", "books"),
               ("ok", "every kid sees themselves")]),
    dict(bg="selfie", framed="tall", lines=["And I'm writing my memoir, *One in a Million.*"],
         pill="The <em>memoir</em>", file="one_in_a_million.md",
         card=[("k", "title", "One in a Million"), ("k", "status", "writing"), ("type", "chapter one")]),
    dict(bg="park", framed=True, lines=["So if your path looks messy right now, *keep going.*"],
         pill="If it looks <em>messy</em>", file="next.sh",
         card=[("k", "path", "messy"), ("cmd", "keep going"), ("ok", "still moving")]),
    dict(bg="friends", lines=["The *scenic route* still gets you there."],
         pill="The scenic <em>route</em>", file="arrival.log",
         card=[("route", "here", "there"), ("k", "route", "scenic"), ("ok", "you still get there")]),
]


def tokenize(sentence):
    """Split into words, tracking *emphasis* spans that may cover several words."""
    out, emph = [], False
    for raw in sentence.split():
        start = raw.startswith("*")
        if start:
            emph = True
        word = raw.replace("*", "")
        out.append((word, emph))
        if raw.rstrip(".,:;!?").endswith("*") or raw.endswith("*"):
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
words = []        # dicts: text, emph, scene, sentence, raw_t
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
for w in words:
    w["t"] = round(0.6 + (w["t"] - 0.6) * scale, 3)
for sc in SCENES:
    sc["start"] = round(0.6 + (sc["raw_start"] - 0.6) * scale, 3) if sc["raw_start"] > 0 else 0.0
for i, sc in enumerate(SCENES):
    nxt = SCENES[i + 1]["start"] if i + 1 < len(SCENES) else TOTAL
    sc["end"] = nxt + (XFADE if i + 1 < len(SCENES) else 0)
caption_end = TOTAL - OUTRO + 0.3

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
    ch_start = ch[0]["t"]
    ch_end = chunks[i + 1][0]["t"] if i + 1 < len(chunks) else caption_end
    for w in ch:
        w["chunk"] = i
    chunks[i] = dict(words=ch, start=ch_start, end=ch_end)

# ---- HTML ---------------------------------------------------------------
esc = html.escape


def card_line(item, sid, n):
    kind = item[0]
    lid = f"s{sid}-l{n}"
    if kind == "cmd":
        return f'<div class="ln" id="{lid}"><span class="pr">&gt;</span> {esc(item[1])}<span class="caret"></span></div>'
    if kind == "k":
        key = f'<span class="key">{esc(item[1])}</span><span class="dim">:</span> ' if item[1] else '<span class="key pad"></span>  '
        return f'<div class="ln" id="{lid}">{key}<span class="val">"{esc(item[2])}"</span></div>'
    if kind == "t":
        return f'<div class="ln dim" id="{lid}">// {esc(item[1])}</div>'
    if kind == "ok":
        return (f'<div class="ln" id="{lid}"><svg class="ic" viewBox="0 0 24 24"><path d="M20 6 9 17l-5-5"/></svg>'
                f'<span class="okt">{esc(item[1])}</span></div>')
    if kind == "err":
        return (f'<div class="ln" id="{lid}"><span class="errk">error</span><span class="dim">:</span> '
                f'<span class="val">{esc(item[1])}</span></div>')
    if kind == "meter":
        return (f'<div class="ln meterln" id="{lid}"><span class="mlabel">{esc(item[1])}</span>'
                f'<span class="meter"><b id="{lid}-fill" style="width:{item[2]}%"></b></span>'
                f'<span class="pct" id="{lid}-pct">{item[2]}%</span></div>')
    if kind == "route":
        return (f'<div class="ln route" id="{lid}"><span class="node">{esc(item[1])}</span>'
                f'<svg class="path" viewBox="0 0 400 24" preserveAspectRatio="none">'
                f'<path id="{lid}-path" d="M4 12 C 90 -6, 150 30, 220 12 S 340 2, 396 12" pathLength="1"/></svg>'
                f'<span class="node to">{esc(item[2])}</span></div>')
    if kind == "scribble":
        return (f'<div class="ln scrib" id="{lid}"><svg viewBox="0 0 600 120">'
                f'<path id="{lid}-path" pathLength="1" d="M10 70 C 60 10, 110 120, 160 60 S 240 0, 270 70 '
                f'S 330 120, 360 50 S 420 10, 450 80 S 520 110, 590 40"/>'
                f'<rect x="120" y="22" width="360" height="76" rx="6" class="box"/></svg></div>')
    if kind == "type":
        return (f'<div class="ln" id="{lid}"><span class="pr">&gt;</span> '
                f'<span class="typed" id="{lid}-typed">{esc(item[1])}</span><span class="caret blink"></span></div>')
    raise ValueError(kind)


sections, js = [], []
for si, sc in enumerate(SCENES):
    dur = round(sc["end"] - sc["start"], 3)
    st = sc["start"]
    bgs = [sc["bg"]] + ([sc["bg2"]] if sc.get("bg2") else [])
    if sc.get("framed"):
        media = (f'<img class="bg" id="s{si}-bg" src="assets/media/{sc["bg"]}-bg.jpg" alt="">'
                 f'<div class="photo{" tall" if sc["framed"] == "tall" else ""}" id="s{si}-photo"><img src="assets/media/{sc["bg"]}.jpg" alt=""></div>')
    else:
        media = "".join(
            f'<img class="bg" id="s{si}-bg{j}" src="assets/media/{b}.jpg" alt="">' for j, b in enumerate(bgs))
    lines = "".join(card_line(it, si, n) for n, it in enumerate(sc["card"]))
    sections.append(f'''
      <section class="clip scene" id="s{si}" data-start="{st}" data-duration="{dur}" data-track-index="1">
        <div class="inner" id="s{si}-inner">
          {media}
          <div class="shade"></div>
          <div class="hud" id="s{si}-hud">
            <div class="pill" id="s{si}-pill">{sc["pill"]}</div>
            <div class="term" id="s{si}-term">
              <div class="bar"><i></i><i></i><i></i><span>{esc(sc["file"])}</span></div>
              <div class="body">{lines}</div>
            </div>
          </div>
        </div>
      </section>''')

    # scene motion (times are absolute on the root timeline)
    if si > 0:
        js.append(f'tl.fromTo("#s{si}-inner", {{opacity: 0}}, {{opacity: 1, duration: {XFADE}, ease: "power1.inOut"}}, {st});')
    if sc.get("framed"):
        js.append(f'tl.fromTo("#s{si}-photo", {{y: 18, rotation: -2.2}}, {{y: 0, rotation: -1.2, duration: 0.7, ease: "power2.out"}}, {st});')
        js.append(f'tl.fromTo("#s{si}-photo img", {{scale: 1}}, {{scale: 1.05, duration: {dur}, ease: "none"}}, {st});')
    elif len(bgs) == 2:
        half = round(dur / 2, 3)
        js.append(f'tl.fromTo("#s{si}-bg0", {{scale: 1.0}}, {{scale: 1.05, duration: {dur}, ease: "none"}}, {st});')
        js.append(f'tl.fromTo("#s{si}-bg1", {{opacity: 0, scale: 1.0}}, {{opacity: 1, scale: 1.03, duration: 0.5, ease: "power1.inOut"}}, {st + half});')
    else:
        js.append(f'tl.fromTo("#s{si}-bg0", {{scale: 1.0}}, {{scale: 1.06, duration: {dur}, ease: "none"}}, {st});')
    hud_in = st + 0.25
    js.append(f'tl.fromTo("#s{si}-pill", {{opacity: 0, y: 4}}, {{opacity: 1, y: 0, duration: 0.3, ease: "power2.out"}}, {hud_in:.3f});')
    js.append(f'tl.fromTo("#s{si}-term", {{opacity: 0, y: 4}}, {{opacity: 1, y: 0, duration: 0.3, ease: "power2.out"}}, {hud_in + 0.12:.3f});')
    for n, it in enumerate(sc["card"]):
        lt = hud_in + 0.45 + n * 0.55
        js.append(f'tl.fromTo("#s{si}-l{n}", {{opacity: 0, x: -4}}, {{opacity: 1, x: 0, duration: 0.22, ease: "power1.out"}}, {lt:.3f});')
        if it[0] == "meter":
            js.append(f'tl.fromTo("#s{si}-l{n}-fill", {{scaleX: 0}}, {{scaleX: 1, duration: 0.9, ease: "power2.out"}}, {lt + 0.1:.3f});')
        if it[0] in ("route", "scribble"):
            js.append(f'tl.fromTo("#s{si}-l{n}-path", {{strokeDashoffset: 1}}, {{strokeDashoffset: 0, duration: 1.1, ease: "power1.inOut"}}, {lt + 0.05:.3f});')
        if it[0] == "type":
            js.append(f'tl.fromTo("#s{si}-l{n}-typed", {{clipPath: "inset(0 100% 0 0)"}}, {{clipPath: "inset(0 0% 0 0)", duration: 1.0, ease: "steps({len(it[1])})"}}, {lt + 0.1:.3f});')
    if si < len(SCENES) - 1:
        out = sc["end"] - XFADE - 0.15
        js.append(f'tl.to("#s{si}-hud", {{opacity: 0, duration: 0.25, ease: "power1.in"}}, {out:.3f});')
    else:
        js.append(f'tl.to("#s{si}-hud", {{opacity: 0, duration: 0.3, ease: "power1.in"}}, {caption_end - 0.3:.3f});')

cap_html = []
for ci, ch in enumerate(chunks):
    spans = []
    for w in ch["words"]:
        cls = "w em" if w["emph"] else "w"
        wid = f"w{words.index(w)}"
        spans.append(f'<span class="{cls}" id="{wid}">{esc(w["text"])}</span>')
        js.append(f'tl.fromTo("#{wid}", {{opacity: 0, y: 5}}, {{opacity: 1, y: 0, duration: 0.14, ease: "power2.out"}}, {w["t"]});')
    cap_html.append(f'<div class="chunk" id="c{ci}">{" ".join(spans)}</div>')
    js.append(f'tl.set("#c{ci}", {{opacity: 1}}, {ch["start"]});')
    js.append(f'tl.set("#c{ci}", {{opacity: 0}}, {ch["end"]});')

outro_t = caption_end + 0.1
js.append(f'tl.fromTo("#outro-sig", {{opacity: 0, y: 4}}, {{opacity: 1, y: 0, duration: 0.36, ease: "power2.out"}}, {outro_t:.3f});')
js.append(f'tl.fromTo("#outro-handle", {{opacity: 0}}, {{opacity: 1, duration: 0.3}}, {outro_t + 0.35:.3f});')

fonts = "\n".join(
    f'@font-face {{ font-family: "{fam}"; src: url("assets/fonts/{f}.woff2") format("woff2"); '
    f'font-weight: {wt}; font-style: {style}; }}'
    for fam, f, wt, style in [
        ("Gelasio", "gelasio-latin-400-normal", 400, "normal"),
        ("Gelasio", "gelasio-latin-400-italic", 400, "italic"),
        ("Gelasio", "gelasio-latin-500-normal", 500, "normal"),
        ("Gelasio", "gelasio-latin-700-normal", 700, "normal"),
        ("Gelasio", "gelasio-latin-700-italic", 700, "italic"),
        ("JetBrains Mono", "jetbrains-mono-latin-400-normal", 400, "normal"),
        ("JetBrains Mono", "jetbrains-mono-latin-500-normal", 500, "normal"),
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
  --blush: #F9B9D2; --pink: #EE3B84; --teal-200: #A6E3DB; --teal: #1E9A99;
}}
body {{ margin: 0; background: var(--ink); }}
#root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: var(--ink);
  font-family: "Gelasio", Georgia, serif; }}
.scene {{ position: absolute; inset: 0; }}
.inner {{ position: absolute; inset: 0; overflow: hidden; }}
.bg {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transform-origin: 50% 40%; }}
.photo {{ position: absolute; left: 200px; top: 540px; width: 680px; height: 907px; padding: 18px;
  background: var(--paper); border-radius: 8px; box-sizing: border-box; overflow: hidden;
  box-shadow: 0 24px 60px rgba(70, 52, 30, 0.35), 0 4px 12px rgba(70, 52, 30, 0.25); }}
.photo.tall {{ left: 230px; width: 620px; height: 1102px; }}
.photo img {{ display: block; width: 100%; height: 100%; object-fit: cover; border-radius: 3px; }}
.shade {{ position: absolute; inset: 0;
  background: linear-gradient(180deg, rgba(20,16,15,0.62) 0%, rgba(20,16,15,0.18) 30%, rgba(20,16,15,0) 45%,
    rgba(20,16,15,0) 58%, rgba(20,16,15,0.55) 78%, rgba(20,16,15,0.72) 100%); }}
.hud {{ position: absolute; left: 0; right: 0; top: 170px; display: flex; flex-direction: column;
  align-items: center; gap: 18px; }}
.pill {{ padding: 12px 30px; border-radius: 999px; background: rgba(34,31,30,0.86); color: var(--cream);
  font-size: 40px; line-height: 1.1; border: 1.5px solid rgba(251,247,238,0.22); }}
.pill em {{ color: var(--blush); font-style: italic; }}
.term {{ width: 760px; border-radius: 16px; background: rgba(34,31,30,0.88); overflow: hidden;
  border: 1.5px solid rgba(251,247,238,0.18); box-shadow: 0 16px 40px rgba(0,0,0,0.3);
  font-family: "JetBrains Mono", monospace; color: var(--cream); }}
.bar {{ display: flex; align-items: center; gap: 10px; padding: 14px 20px; background: rgba(251,247,238,0.06);
  border-bottom: 1px solid rgba(251,247,238,0.1); }}
.bar i {{ width: 13px; height: 13px; border-radius: 50%; background: var(--pink); }}
.bar i:nth-child(2) {{ background: var(--sand); }}
.bar i:nth-child(3) {{ background: var(--teal); }}
.bar span {{ margin-left: auto; font-size: 22px; color: rgba(251,247,238,0.6); letter-spacing: 0.04em; }}
.body {{ padding: 20px 28px 24px; display: flex; flex-direction: column; gap: 12px; font-size: 30px; line-height: 1.3; }}
.ln {{ display: flex; align-items: center; white-space: nowrap; }}
.pr {{ color: var(--blush); margin-right: 12px; }}
.key {{ color: var(--teal-200); }}
.key.pad {{ display: inline-block; width: 4ch; }}
.val {{ color: var(--blush); margin-left: 12px; }}
.dim {{ color: rgba(251,247,238,0.55); }}
.errk {{ color: #F27A9F; }}
.ic {{ width: 32px; height: 32px; margin-right: 14px; fill: none; stroke: var(--teal-200); stroke-width: 2.6;
  stroke-linecap: round; stroke-linejoin: round; }}
.okt {{ color: var(--cream); }}
.caret {{ display: inline-block; width: 14px; height: 30px; margin-left: 8px; background: var(--blush); }}
.meterln {{ gap: 16px; }}
.mlabel {{ flex: none; color: var(--teal-200); }}
.meter {{ flex: 1; height: 18px; border-radius: 9px; background: rgba(251,247,238,0.12); overflow: hidden; }}
.meter b {{ display: block; height: 100%; border-radius: 9px; background: var(--blush); transform-origin: 0 50%; }}
.pct {{ width: 4ch; text-align: right; color: rgba(251,247,238,0.7); }}
.route {{ gap: 16px; }}
.node {{ padding: 2px 14px; border-radius: 8px; border: 1.5px solid var(--teal-200); color: var(--teal-200); }}
.node.to {{ border-color: var(--blush); color: var(--blush); }}
.path {{ flex: 1; height: 28px; overflow: visible; }}
.path path, .scrib path {{ fill: none; stroke: var(--blush); stroke-width: 4; stroke-linecap: round;
  stroke-dasharray: 1; vector-effect: non-scaling-stroke; }}
.scrib svg {{ width: 100%; height: 120px; }}
.scrib .box {{ fill: none; stroke: rgba(166,227,219,0.55); stroke-width: 2.5; stroke-dasharray: 10 8; }}
.typed {{ display: inline-block; color: var(--cream); }}
.captions {{ position: absolute; left: 70px; right: 70px; bottom: 430px; height: 260px; }}
.chunk {{ position: absolute; inset: 0; display: flex; flex-wrap: wrap; align-content: flex-end;
  justify-content: center; column-gap: 20px; opacity: 0; text-align: center; }}
.w {{ display: inline-block; color: #FFFFFF; font-weight: 700; font-size: 84px; line-height: 1.12;
  text-shadow: 0 3px 0 rgba(34,31,30,0.55), 0 6px 22px rgba(20,16,15,0.75); }}
.w.em {{ color: var(--blush); font-style: italic; }}
.outro {{ position: absolute; left: 0; right: 0; bottom: 300px; display: flex; flex-direction: column;
  align-items: center; gap: 10px; }}
#outro-sig {{ font-size: 96px; font-style: italic; color: var(--blush); text-shadow: 0 4px 20px rgba(20,16,15,0.7); }}
#outro-handle {{ font-family: "JetBrains Mono", monospace; font-size: 30px; color: var(--cream);
  letter-spacing: 0.06em; text-shadow: 0 2px 12px rgba(20,16,15,0.8); }}
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
for sc in SCENES:
    print(f'  {sc["start"]:6.2f}-{sc["end"]:6.2f}  {sc["bg"]}')
