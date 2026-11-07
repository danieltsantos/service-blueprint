#!/usr/bin/env python3
# service-blueprint skill. Copyright 2026 Daniel Santos (danieltsantos.com). CC BY-NC 4.0, see LICENSE.txt.
"""Render a service blueprint (frame YAML + card CSV) as one self-contained HTML page.

Usage:
  python render_html.py <frame.yaml> <cards.csv> -o <out.html>

The page follows the claude.ai Artifact page contract (no <html>/<head>/<body> tags,
theme tokens, phone-safe gutters), so it can be published as-is with the Artifact tool.
It also opens fine as a local file.
"""
import argparse
import html
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bp  # noqa: E402

E = html.escape
REL_RANK = {"": 1, "R1": 1, "R2": 2, "R3": 3, "RX": 4, "TBC": 4}
LINE_LABEL = {"interaction": "Line of interaction", "visibility": "Line of visibility",
              "internal": "Line of internal interaction"}
LINE_LABEL_PT = {"interaction": "Linha de interação", "visibility": "Linha de visibilidade",
                 "internal": "Linha de interação interna"}
TYPE_LABEL = {"start": "Start / end", "task": "Task", "system": "System", "gate": "Gate",
              "message": "Message", "agent": "AI agent", "exception": "Exception",
              "question": "Question", "decision": "Decision", "gap": "Gap",
              "friction": "Friction", "idea": "Idea", "evidence": "Evidence", "artefact": "Artefact"}


def text(s):
    return E(s or "").replace("\\n", "<br>").replace("\n", "<br>")


def card_html(c):
    cls = [f"card", f"t-{c['type']}", f"b-{c['basis']}"]
    if c["type"] == "exception" and c["exc_status"]:
        cls.append(f"e-{c['exc_status']}")
    if c["type"] in bp.STICKIES:
        cls.append("sticky")
    rel = c["release"]
    badges = []
    if rel:
        badges.append(f'<span class="pill rel rel-{E(rel)}">{E(rel)}</span>')
    for v in [v.strip() for v in c["variant"].split(";") if v.strip()]:
        badges.append(f'<span class="pill var">{E(v)}</span>')
    if c["basis"] in bp.UNVERIFIED:
        badges.append(f'<span class="pill basis basis-{c["basis"]}">{E(c["basis"].upper() if c["basis"] == "tbc" else c["basis"])}</span>')
    if c["type"] == "exception" and c["exc_status"]:
        badges.append(f'<span class="pill exc">{E(c["exc_status"])}</span>')
    parts = [f'<div class="card-top"><span class="cid">{E(c["id"])}</span>{"".join(badges)}</div>',
             f'<div class="ctitle">{text(c["title"])}</div>']
    if c["type"] in {"start", "end"}:
        return (f'<div class="{" ".join(cls)}" id="c-{E(c["id"])}" data-id="{E(c["id"])}" '
                f'data-rel="{REL_RANK.get(rel, 4)}" data-variant="{E(c["variant"])}" tabindex="0">'
                + "".join(parts) + "</div>")
    if c["body"]:
        parts.append(f'<div class="cbody">{text(c["body"])}</div>')
    if c["cx_status"]:
        parts.append(f'<div class="status"><span>CX status</span> {E(c["cx_status"])}</div>')
    meta = []
    if c["trigger"]:
        meta.append(f"<dt>Trigger</dt><dd>{text(c['trigger'])}</dd>")
    if c["metric"]:
        meta.append(f"<dt>Metric</dt><dd>{text(c['metric'])}</dd>")
    if c["owner"]:
        cls_o = ' class="unowned"' if c["owner"].lower() == "unassigned" else ""
        meta.append(f"<dt>Owner</dt><dd{cls_o}>{E(c['owner'])}</dd>")
    if c["cx_risk"]:
        meta.append(f"<dt>CX risk</dt><dd>{text(c['cx_risk'])}</dd>")
    if c["source"]:
        meta.append(f"<dt>Source</dt><dd>{E(c['source'].replace(';', ', '))}</dd>")
    if meta:
        parts.append(f'<dl class="cmeta">{"".join(meta)}</dl>')
    return (f'<div class="{" ".join(cls)}" id="c-{E(c["id"])}" data-id="{E(c["id"])}" '
            f'data-rel="{REL_RANK.get(rel, 4)}" data-variant="{E(c["variant"])}" tabindex="0">'
            + "".join(parts) + "</div>")


def build(frame, cards):
    lanes, lines = bp.lane_list(frame)
    cols = bp.phase_columns(frame, cards)
    ncols = sum(n for _, n in cols.values()) or 1
    pt = str(frame.get("language", "en")).lower().startswith("pt")
    line_label = LINE_LABEL_PT if pt else LINE_LABEL

    cells = defaultdict(list)
    for c in cards:
        if c["phase"] in cols:
            start, n = cols[c["phase"]]
            col = start + min(max(c["_step"], 1), n) - 1
            cells[(c["lane"], col)].append(c)
    phase_starts = {start for start, _ in cols.values()}

    rows = []
    r = 1
    # phase name row
    rows.append(f'<div class="rlabel head" style="grid-row:{r}">{"Fases" if pt else "Phases"}</div>')
    for p in frame["phases"]:
        start, n = cols[p["id"]]
        rows.append(f'<div class="phase" style="grid-row:{r};grid-column:{start + 2} / span {n}">'
                    f'<div class="pnum">{"Fase" if pt else "Phase"} {E(p["id"])}</div>'
                    f'<div class="pname">{E(p.get("name", ""))}</div>'
                    f'<div class="psub">{E(p.get("subtitle", ""))}</div></div>')
    r += 1
    rows.append(f'<div class="rlabel head" style="grid-row:{r}">CX · SLA</div>')
    for p in frame["phases"]:
        start, n = cols[p["id"]]
        rows.append(f'<div class="timeline" style="grid-row:{r};grid-column:{start + 2} / span {n}">'
                    f'<div class="cx"><b>CX</b> {E(str(p.get("cx", "")))}</div>'
                    f'<div class="sla"><b>SLA</b> {E(str(p.get("sla", "") or "TBC"))}</div></div>')
    r += 1

    def line_row(kind):
        nonlocal r
        rows.append(f'<div class="rlabel line line-{kind}" style="grid-row:{r}">{E(line_label.get(kind, kind))}</div>'
                    f'<div class="lrule line-{kind}" style="grid-row:{r};grid-column:2 / span {ncols}"></div>')
        r += 1

    for lane in lanes:
        for kind, idx in lines.items():
            if idx == lane["_idx"]:
                line_row(kind)
        note = f'<span class="lnote">{E(str(lane.get("note", "")))}</span>' if lane.get("note") else ""
        rows.append(f'<div class="rlabel lane z-{E(lane["zone"])}" style="grid-row:{r}">'
                    f'<span class="lname">{E(str(lane.get("name", lane["id"])))}</span>{note}</div>')
        for col in range(ncols):
            content = "".join(card_html(c) for c in cells.get((lane["id"], col), []))
            ps = " pstart" if col in phase_starts else ""
            rows.append(f'<div class="cell z-{E(lane["zone"])}{ps}" style="grid-row:{r};grid-column:{col + 2}">{content}</div>')
        r += 1
    for kind, idx in lines.items():
        if idx >= len(lanes):
            line_row(kind)

    links = []
    for c in cards:
        for target, ltype, label in bp.parse_links(c["links"]):
            links.append({"from": c["id"], "to": target, "type": ltype, "label": label})

    errors, quality = bp.check(frame, cards)
    decisions = bp.decision_list(cards)
    return rows, ncols, links, errors, quality, decisions


def page(frame, cards):
    rows, ncols, links, errors, quality, decisions = build(frame, cards)
    title = str(frame.get("title", "Service blueprint"))
    meta_bits = [("Owner", frame.get("owner")), ("Updated", frame.get("last_updated")),
                 ("State", frame.get("state")), ("Layer", frame.get("layer")), ("Status", frame.get("status"))]
    parent = frame.get("parent") or {}
    if isinstance(parent, dict) and parent.get("title"):
        meta_bits.append(("Expands", f'{parent["title"]}' + (f' cards {parent["expands"]}' if parent.get("expands") else "")))
    att_top = frame.get("attribution") or {}
    if isinstance(att_top, dict) and att_top.get("author"):
        meta_bits.append(("By", att_top["author"]))
        if att_top.get("licence"):
            meta_bits.append(("Licence", att_top["licence"]))
    meta = " · ".join(f"<span><b>{k}</b> {E(str(v))}</span>" for k, v in meta_bits if v)

    header_boxes = []
    for box in frame["header"]:
        items = "".join(f"<li>{E(str(i))}</li>" for i in box.get("items", []))
        header_boxes.append(f'<section class="hbox"><h3>{E(str(box.get("heading", "")))}</h3><ul>{items}</ul></section>')

    present = sorted({c["type"] for c in cards} - {"end"}, key=list(TYPE_LABEL).index)
    legend_types = "".join(f'<span class="lg"><i class="sw t-{t}"></i>{TYPE_LABEL[t]}</span>' for t in present)
    legend_links = "".join(
        f'<span class="lg"><svg width="34" height="10" aria-hidden="true"><line x1="1" y1="5" x2="33" y2="5" class="l-{t}"/></svg>{n}</span>'
        for t, n in [("action", "Action flow"), ("system", "System / dependency"),
                     ("message", "Message to customer"), ("artefact", "Link to artefact")])

    variants = sorted({v.strip() for c in cards for v in c["variant"].split(";") if v.strip()})
    var_ctrl = ""
    if variants:
        opts = "".join(f'<option value="{E(v)}">{E(v)}</option>' for v in variants)
        var_ctrl = f'<label for="f-var">Variant <select id="f-var"><option value="">All</option>{opts}</select></label>'
    has_rel = any(c["release"] for c in cards)
    rel_ctrl = ('<label for="f-rel">Release <select id="f-rel"><option value="9">All</option>'
                '<option value="1">R1</option><option value="2">Up to R2</option><option value="3">Up to R3</option></select></label>') if has_rel else ""

    passed = sum(q["passed"] for q in quality)
    checks = "".join(
        f'<li class="{"ok" if q["passed"] else "bad"}"><b>{q["id"]}</b> {E(q["name"])}'
        + ("" if q["passed"] else "<ul>" + "".join(f"<li>{E(d)}</li>" for d in q["details"][:10]) + "</ul>")
        + "</li>" for q in quality)
    if errors:
        checks = "".join(f'<li class="bad"><b>Format</b> {E(e)}</li>' for e in errors[:20]) + checks
    dec = "".join(f'<li><span class="pill">{E(k)}</span> <a href="#c-{E(c["id"])}">{E(c["id"])}</a> {E(c["title"])}'
                  + (f' <em>Owner: {E(c["owner"])}</em>' if c["owner"] else "") + "</li>" for k, c in decisions)

    by_status = defaultdict(list)
    pats = bp.state_patterns(frame)
    for c in cards:
        for m, n, rx in pats:
            if c["cx_status"] and rx.match(c["cx_status"]):
                by_status[(m, n)].append(c["id"])
    models = ""
    for model in frame["status_models"]:
        trs = ""
        for s in model.get("states", []):
            ids = by_status[(model.get("name", ""), str(s.get("name", "")).strip())]
            setters = ", ".join('<a href="#c-%s">%s</a>' % (E(i), E(i)) for i in ids) or '<span class="unowned">none</span>'
            trs += (f'<tr><td>{E(str(s.get("name", "")))}</td><td>{E(str(s.get("set_by", "")))}</td>'
                    f'<td>{setters}</td></tr>')
        models += (f'<section class="model"><h3>{E(str(model.get("name", "")))}</h3><div class="tablewrap"><table>'
                   f'<thead><tr><th>State</th><th>Set by</th><th>Cards</th></tr></thead><tbody>{trs}</tbody></table></div></section>')
    sources = "".join(
        f'<li><span class="pill src-{E(str(s.get("type", "")))}">{E(str(s.get("type", "")))}</span> '
        f'<b>{E(str(s.get("id", "")))}</b> {E(str(s.get("name", "")))}'
        + (f' <span class="muted">{E(str(s.get("date", "")))}</span>' if s.get("date") else "")
        + (f' <a href="{E(str(s["link"]))}" target="_blank" rel="noopener">link</a>' if s.get("link") else "")
        + "</li>" for s in frame["sources"])
    policy = f'<p class="policy"><b>Lane placement</b> {E(str(frame["lane_policy"]))}</p>' if frame.get("lane_policy") else ""
    att = frame.get("attribution") or {}
    footer = ""
    if isinstance(att, dict) and att.get("author"):
        who = E(str(att["author"]))
        if att.get("url"):
            who = f'<a href="{E(str(att["url"]))}" target="_blank" rel="noopener">{who}</a>'
        lic = E(str(att.get("licence", "")))
        if lic and att.get("licence_url"):
            lic = f'<a href="{E(str(att["licence_url"]))}" target="_blank" rel="noopener">{lic}</a>'
        year = E(str(att.get("year", "")))
        footer = (f'<footer class="credit">&copy; {year + " " if year else ""}{who}'
                  + (f' &middot; Licensed under {lic}' if lic else "")
                  + (f' &middot; {E(str(att["note"]))}' if att.get("note") else "") + "</footer>")

    return TEMPLATE.format(
        title=E(title), deliverable=E(str(frame.get("deliverable", ""))), meta=meta,
        header="".join(header_boxes), legend_types=legend_types, legend_links=legend_links,
        controls=rel_ctrl + var_ctrl, ncols=ncols, rows="".join(rows),
        links=json.dumps(links, ensure_ascii=False).replace("</", "<\\/"),
        passed=passed, total=len(quality), checks=checks, decisions=dec or "<li>None</li>",
        ndec=len(decisions), models=models or "<p class=muted>No status models defined.</p>",
        sources=sources or "<li>None listed</li>", policy=policy, footer=footer)


TEMPLATE = """<title>{title}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Barlow+Condensed:wght@500;600;700&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
/* Layout: an operations board. Fixed label column, one grid column per step, lanes as bands, the three lines as coloured rules. */
:root {{
  --bg: #f3f4f1; --fg: #1d2421; --muted: #5d6762; --rule: #c9cec9; --surface: #ffffff; --band: #e9ebe6; --band-alt: #eef0eb;
  --accent: #1f5f8b;
  --z-evidence: #e7e0cf; --z-customer: #1d2421; --z-customer-fg: #ffffff; --z-frontstage: #d9e6ef; --z-backstage: #e6dfee;
  --z-support: #dfe8df; --z-artefacts: #e4efe2; --z-exceptions: #f6e4d6;
  --t-system: #dcebf7; --t-system-b: #5f93bd; --t-gate: #fff4c7; --t-gate-b: #c9a227; --t-message: #eceeed; --t-message-b: #8b928e;
  --t-agent: #ebe3f8; --t-agent-b: #7a5bbd; --t-exc: #fbe1df; --t-exc-b: #c2413b; --t-risk: #fdebd3; --t-risk-b: #d07a1c;
  --s-question: #fff2a8; --s-decision: #d4f0cf; --s-gap: #fbd9e6; --s-friction: #ffdcbc; --s-idea: #e3f4d6; --t-evidence: #d7efeb; --t-evidence-b: #2d8a7d;
  --l-action: #2b322e; --l-system: #7c8580; --l-message: #2a6fb0; --l-artefact: #9aa29d;
  --line-interaction: #2e8b57; --line-visibility: #2a6fb0; --line-internal: #1b9aa8;
  --rel: #116d73; --rel-fg: #ffffff; --warn: #b3261e;
  --f-display: "Barlow Condensed", "Arial Narrow", "Roboto Condensed", sans-serif;
  --f-body: "Atkinson Hyperlegible", system-ui, -apple-system, "Segoe UI", sans-serif;
  --f-mono: "IBM Plex Mono", ui-monospace, "SF Mono", Menlo, monospace;
  --col-w: 212px; --label-w: 148px;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #151a18; --fg: #e4e9e5; --muted: #9aa49f; --rule: #3a423e; --surface: #1f2522; --band: #1b211e; --band-alt: #19201d;
  --accent: #7fb6dc;
  --z-evidence: #3a3528; --z-customer: #e4e9e5; --z-customer-fg: #151a18; --z-frontstage: #20323f; --z-backstage: #2e2839;
  --z-support: #23322a; --z-artefacts: #253326; --z-exceptions: #3d2c21;
  --t-system: #1d3142; --t-system-b: #6ea3cf; --t-gate: #3b3415; --t-gate-b: #d8b43c; --t-message: #2a302d; --t-message-b: #8b928e;
  --t-agent: #2f2742; --t-agent-b: #a88be6; --t-exc: #45211f; --t-exc-b: #e0645d; --t-risk: #42301b; --t-risk-b: #e59a45;
  --s-question: #4a4419; --s-decision: #24402a; --s-gap: #46283a; --s-friction: #4a3420; --s-idea: #2d3d22; --t-evidence: #173b36; --t-evidence-b: #4fb6a6;
  --l-action: #d4dbd6; --l-system: #8e9893; --l-message: #6aa8e0; --l-artefact: #6b746f;
  --line-interaction: #5cc189; --line-visibility: #6aa8e0; --line-internal: #4cc3cf;
  --rel: #3fb0b6; --rel-fg: #0d1513; --warn: #f08a82; color-scheme: dark;
}} }}
:root[data-theme="dark"] {{
  --bg: #151a18; --fg: #e4e9e5; --muted: #9aa49f; --rule: #3a423e; --surface: #1f2522; --band: #1b211e; --band-alt: #19201d;
  --accent: #7fb6dc;
  --z-evidence: #3a3528; --z-customer: #e4e9e5; --z-customer-fg: #151a18; --z-frontstage: #20323f; --z-backstage: #2e2839;
  --z-support: #23322a; --z-artefacts: #253326; --z-exceptions: #3d2c21;
  --t-system: #1d3142; --t-system-b: #6ea3cf; --t-gate: #3b3415; --t-gate-b: #d8b43c; --t-message: #2a302d; --t-message-b: #8b928e;
  --t-agent: #2f2742; --t-agent-b: #a88be6; --t-exc: #45211f; --t-exc-b: #e0645d; --t-risk: #42301b; --t-risk-b: #e59a45;
  --s-question: #4a4419; --s-decision: #24402a; --s-gap: #46283a; --s-friction: #4a3420; --s-idea: #2d3d22; --t-evidence: #173b36; --t-evidence-b: #4fb6a6;
  --l-action: #d4dbd6; --l-system: #8e9893; --l-message: #6aa8e0; --l-artefact: #6b746f;
  --line-interaction: #5cc189; --line-visibility: #6aa8e0; --line-internal: #4cc3cf;
  --rel: #3fb0b6; --rel-fg: #0d1513; --warn: #f08a82; color-scheme: dark;
}}
body {{ background: var(--bg); color: var(--fg); font-family: var(--f-body); font-size: 14px; line-height: 1.45; }}
.wrap {{ padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); padding-block: 20px 48px; display: grid; gap: 20px; }}
h1 {{ font-family: var(--f-display); font-weight: 700; font-size: clamp(28px, 4vw, 40px); line-height: 1.05; margin: 0; text-wrap: balance; }}
h2 {{ font-family: var(--f-display); font-weight: 600; font-size: 22px; margin: 0 0 8px; letter-spacing: .01em; }}
h3 {{ font-family: var(--f-display); font-weight: 600; font-size: 15px; text-transform: uppercase; letter-spacing: .06em; margin: 0 0 6px; color: var(--muted); }}
.deliverable {{ margin: 4px 0 0; color: var(--muted); max-width: 70ch; }}
.meta {{ display: flex; flex-wrap: wrap; gap: 4px 14px; font-size: 13px; color: var(--muted); margin-top: 8px; }}
.meta b {{ color: var(--fg); font-weight: 700; }}
.hgrid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; }}
.hbox {{ background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 10px 12px; min-width: 0; }}
.hbox ul {{ margin: 0; padding-left: 18px; }}
.legend {{ display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: center; font-size: 12.5px; color: var(--muted); }}
.lg {{ display: inline-flex; align-items: center; gap: 6px; }}
.sw {{ width: 14px; height: 12px; border-radius: 2px; border: 1.5px solid var(--rule); background: var(--surface); display: inline-block; }}
.sw.t-start {{ background: var(--fg); border-color: var(--fg); border-radius: 50%; width: 12px; }}
.sw.t-gate {{ transform: rotate(45deg); width: 10px; height: 10px; }}
.policy {{ margin: 0; font-size: 13px; color: var(--muted); }}
.controls {{ display: flex; flex-wrap: wrap; gap: 10px 18px; align-items: center; font-size: 13px; }}
.controls label {{ display: inline-flex; gap: 6px; align-items: center; }}
.controls select {{ font: inherit; padding: 3px 6px; border-radius: 4px; border: 1px solid var(--rule); background: var(--surface); color: var(--fg); }}
.controls input:focus-visible, .controls select:focus-visible, .card:focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; }}
.boardwrap {{ overflow-x: auto; border: 1px solid var(--rule); border-radius: 6px; background: var(--band); }}
.board {{ position: relative; display: grid; grid-template-columns: var(--label-w) repeat({ncols}, var(--col-w)); width: max-content; }}
.board > svg {{ position: absolute; inset: 0 auto auto 0; pointer-events: none; z-index: 1; overflow: visible; }}
.rlabel {{ position: sticky; left: 0; z-index: 4; padding: 10px; font-family: var(--f-display); font-size: 14px; letter-spacing: .04em; text-transform: uppercase; font-weight: 600; background: var(--band); border-right: 1px solid var(--rule); display: flex; flex-direction: column; justify-content: center; gap: 2px; }}
.rlabel.head {{ color: var(--muted); font-size: 12px; }}
.rlabel.lane {{ border-bottom: 1px solid var(--rule); }}
.lnote {{ font-family: var(--f-body); text-transform: none; letter-spacing: 0; font-weight: 400; font-size: 11.5px; color: var(--muted); line-height: 1.3; }}
.rlabel.z-customer {{ background: var(--z-customer); color: var(--z-customer-fg); }}
.rlabel.z-customer .lnote {{ color: inherit; opacity: .75; }}
.rlabel.z-evidence {{ background: var(--z-evidence); }} .rlabel.z-frontstage {{ background: var(--z-frontstage); }}
.rlabel.z-backstage {{ background: var(--z-backstage); }} .rlabel.z-support {{ background: var(--z-support); }}
.rlabel.z-artefacts {{ background: var(--z-artefacts); }} .rlabel.z-exceptions {{ background: var(--z-exceptions); }}
.phase {{ padding: 10px 12px 6px; border-left: 3px solid var(--fg); background: var(--surface); z-index: 2; }}
.pnum {{ font-family: var(--f-mono); font-size: 11px; color: var(--muted); }}
.pname {{ font-family: var(--f-display); font-weight: 700; font-size: 20px; line-height: 1.1; }}
.psub {{ font-size: 12.5px; color: var(--muted); }}
.timeline {{ padding: 6px 12px 10px; border-left: 3px solid var(--fg); background: var(--surface); font-size: 12.5px; border-bottom: 1px solid var(--rule); z-index: 2; }}
.timeline b {{ font-family: var(--f-mono); font-size: 10.5px; font-weight: 500; color: var(--muted); margin-right: 4px; }}
.sla {{ color: var(--muted); }}
.rlabel.line {{ font-size: 11px; padding: 2px 10px; min-height: 22px; background: var(--band); }}
.lrule {{ align-self: center; height: 0; border-top: 2px dashed; z-index: 2; }}
.line-interaction {{ color: var(--line-interaction); border-color: var(--line-interaction); }}
.line-visibility {{ color: var(--line-visibility); border-color: var(--line-visibility); }}
.line-internal {{ color: var(--line-internal); border-color: var(--line-internal); }}
.cell {{ padding: 8px; display: flex; flex-direction: column; gap: 8px; border-bottom: 1px solid var(--rule); min-width: 0; background: var(--band-alt); }}
.cell.pstart {{ border-left: 3px solid var(--rule); }}
.cell.z-customer {{ background: var(--band); }}
.card {{ position: relative; z-index: 2; background: var(--surface); border: 1.5px solid var(--rule); border-radius: 5px; padding: 6px 8px 7px; font-size: 12.5px; line-height: 1.35; min-width: 0; overflow-wrap: anywhere; transition: opacity .15s; }}
.card-top {{ display: flex; flex-wrap: wrap; gap: 4px; align-items: center; margin-bottom: 2px; }}
.cid {{ font-family: var(--f-mono); font-size: 10.5px; color: var(--muted); margin-right: 2px; }}
.ctitle {{ font-weight: 700; }}
.cbody {{ color: var(--fg); margin-top: 2px; }}
.status {{ margin-top: 5px; font-size: 11.5px; }}
.status span {{ font-family: var(--f-mono); font-size: 10px; color: var(--muted); }}
.cmeta {{ margin: 5px 0 0; display: grid; grid-template-columns: auto 1fr; gap: 1px 6px; font-size: 11.5px; }}
.cmeta dt {{ font-family: var(--f-mono); font-size: 10px; color: var(--muted); padding-top: 1px; }}
.cmeta dd {{ margin: 0; min-width: 0; }}
.unowned {{ color: var(--warn); font-weight: 700; }}
.pill {{ font-family: var(--f-mono); font-size: 10px; line-height: 1; padding: 3px 5px; border-radius: 3px; background: var(--band); color: var(--muted); border: 1px solid var(--rule); }}
.pill.rel {{ background: var(--rel); color: var(--rel-fg); border-color: transparent; }}
.pill.basis {{ border-style: dashed; color: var(--fg); }}
.pill.exc {{ text-transform: uppercase; }}
.t-start, .t-end {{ background: var(--fg); color: var(--bg); border-color: var(--fg); border-radius: 999px; text-align: center; }}
.t-start .cid, .t-end .cid {{ color: inherit; opacity: .7; }}
.t-start .card-top, .t-end .card-top {{ justify-content: center; }}
.t-system {{ background: var(--t-system); border-color: var(--t-system-b); }}
.t-gate {{ background: var(--t-gate); border-color: var(--t-gate-b); }}
.t-gate .ctitle::before {{ content: "\\25C6  "; color: var(--t-gate-b); }}
.t-message {{ background: var(--t-message); border-color: var(--t-message-b); }}
.t-agent {{ background: var(--t-agent); border-color: var(--t-agent-b); }}
.t-exception {{ background: var(--t-exc); border-color: var(--t-exc-b); }}
.t-exception.e-workaround, .t-exception.e-risk {{ background: var(--t-risk); border-color: var(--t-risk-b); }}
.t-exception.e-decided {{ background: var(--surface); border-color: var(--rule); }}
.t-evidence {{ background: var(--t-evidence); border-color: var(--t-evidence-b); }}
.t-artefact {{ border-style: dotted; }}
.sticky {{ border: none; border-radius: 2px; box-shadow: 0 1px 2px rgb(0 0 0 / .18); }}
.t-question {{ background: var(--s-question); }} .t-decision {{ background: var(--s-decision); }} .t-gap {{ background: var(--s-gap); }}
.t-friction {{ background: var(--s-friction); }} .t-idea {{ background: var(--s-idea); }}
.sw.t-system {{ background: var(--t-system); border-color: var(--t-system-b); }} .sw.t-gate {{ background: var(--t-gate); border-color: var(--t-gate-b); }}
.sw.t-message {{ background: var(--t-message); border-color: var(--t-message-b); }} .sw.t-agent {{ background: var(--t-agent); border-color: var(--t-agent-b); }}
.sw.t-exception {{ background: var(--t-exc); border-color: var(--t-exc-b); }} .sw.t-evidence {{ background: var(--t-evidence); border-color: var(--t-evidence-b); }}
.sw.t-question {{ background: var(--s-question); border: 0; }} .sw.t-decision {{ background: var(--s-decision); border: 0; }} .sw.t-gap {{ background: var(--s-gap); border: 0; }}
.sw.t-friction {{ background: var(--s-friction); border: 0; }} .sw.t-idea {{ background: var(--s-idea); border: 0; }} .sw.t-artefact {{ border-style: dotted; }}
.b-tbc.t-task, .b-tbc.t-system {{ border-style: dashed; }}
.board.spotlight .card.b-evidence, .board.spotlight .card.b-decided {{ opacity: .28; }}
.card.dim {{ opacity: .18; }}
.board.tracing .card:not(.hl) {{ opacity: .3; }}
.board.tracing path:not(.hl), .board.tracing text:not(.hl) {{ opacity: .12; }}
path {{ fill: none; stroke-width: 1.6; }}
line.l-action, path.l-action {{ stroke: var(--l-action); }}
line.l-system, path.l-system {{ stroke: var(--l-system); stroke-dasharray: 6 4; }}
line.l-message, path.l-message {{ stroke: var(--l-message); stroke-dasharray: 7 4; }}
line.l-artefact, path.l-artefact {{ stroke: var(--l-artefact); stroke-dasharray: 2 3; }}
line {{ stroke-width: 2; }}
path.hl {{ stroke-width: 2.6; }}
path.dimlink {{ opacity: .12; }}
.mk-action {{ fill: var(--l-action); }} .mk-system {{ fill: var(--l-system); }} .mk-message {{ fill: var(--l-message); }} .mk-artefact {{ fill: var(--l-artefact); }}
svg text {{ font-family: var(--f-mono); font-size: 10.5px; fill: var(--fg); paint-order: stroke; stroke: var(--band-alt); stroke-width: 4px; stroke-linejoin: round; }}
.lower {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; align-items: start; }}
.panel {{ background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 12px 14px; min-width: 0; }}
.panel ul {{ margin: 0; padding-left: 18px; display: grid; gap: 4px; }}
.checks > li.ok::marker {{ content: "✓  "; color: var(--line-interaction); }}
.checks > li.bad::marker {{ content: "✕  "; color: var(--warn); }}
.checks ul {{ color: var(--muted); font-size: 12.5px; }}
.panel a {{ color: var(--accent); }}
.muted {{ color: var(--muted); }}
.tablewrap {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ text-align: left; padding: 4px 8px 4px 0; border-bottom: 1px solid var(--rule); vertical-align: top; }}
th {{ font-family: var(--f-display); font-weight: 600; text-transform: uppercase; letter-spacing: .05em; font-size: 12px; color: var(--muted); }}
.model + .model {{ margin-top: 12px; }}
.src-ai-synthesis {{ border-color: var(--t-risk-b); color: var(--fg); }}
.hint {{ font-size: 12.5px; color: var(--muted); margin: 0; }}
.credit {{ font-size: 12.5px; color: var(--muted); border-top: 1px solid var(--rule); padding-top: 12px; }}
.credit a {{ color: var(--accent); }}
@media (prefers-reduced-motion: reduce) {{ .card {{ transition: none; }} }}
@media (max-width: 600px) {{ :root {{ --label-w: 104px; --col-w: 188px; }} .rlabel {{ font-size: 12px; padding: 8px 6px; }} }}
</style>

<div class="wrap">
  <header>
    <h1>{title}</h1>
    <p class="deliverable">{deliverable}</p>
    <div class="meta">{meta}</div>
  </header>
  <div class="hgrid">{header}</div>
  <div class="legend">{legend_types}{legend_links}</div>
  {policy}
  <div class="controls">
    {controls}
    <label for="f-links"><input type="checkbox" id="f-links" checked> Connectors</label>
    <label for="f-spot"><input type="checkbox" id="f-spot"> Spotlight unverified cards</label>
  </div>
  <p class="hint">Hover or tap a card to trace its connections. Tap again to clear.</p>
  <div class="boardwrap"><div class="board" id="board">
    <svg id="links" aria-hidden="true"><defs></defs></svg>
    {rows}
  </div></div>
  <div class="lower">
    <section class="panel"><h2>Needs a decision ({ndec})</h2><ul>{decisions}</ul></section>
    <section class="panel"><h2>Quality checks {passed}/{total}</h2><ul class="checks">{checks}</ul></section>
    <section class="panel"><h2>Status models</h2>{models}</section>
    <section class="panel"><h2>Sources</h2><ul>{sources}</ul></section>
  </div>
  {footer}
</div>

<script id="bp-links" type="application/json">{links}</script>
<script>
(function () {{
  const LINKS = JSON.parse(document.getElementById('bp-links').textContent);
  const board = document.getElementById('board');
  const svg = document.getElementById('links');
  const NS = 'http://www.w3.org/2000/svg';
  const defs = svg.querySelector('defs');
  ['action', 'system', 'message', 'artefact'].forEach(t => {{
    const m = document.createElementNS(NS, 'marker');
    m.setAttribute('id', 'ar-' + t); m.setAttribute('viewBox', '0 0 10 10'); m.setAttribute('refX', '9'); m.setAttribute('refY', '5');
    m.setAttribute('markerWidth', '7'); m.setAttribute('markerHeight', '7'); m.setAttribute('orient', 'auto-start-reverse');
    const p = document.createElementNS(NS, 'path'); p.setAttribute('d', 'M0,0 L10,5 L0,10 z'); p.setAttribute('class', 'mk-' + t);
    p.style.stroke = 'none'; m.appendChild(p); defs.appendChild(m);
  }});
  const el = id => document.getElementById('c-' + id);
  function box(e, b) {{ const r = e.getBoundingClientRect(); return {{ l: r.left - b.left, t: r.top - b.top, r: r.right - b.left, b: r.bottom - b.top, w: r.width, h: r.height }}; }}
  function draw() {{
    svg.querySelectorAll('path:not(defs path), text').forEach(n => n.remove());
    svg.setAttribute('width', board.scrollWidth); svg.setAttribute('height', board.scrollHeight);
    const B = board.getBoundingClientRect();
    LINKS.forEach(L => {{
      const a = el(L.from), z = el(L.to); if (!a || !z) return;
      const s = box(a, B), t = box(z, B);
      const scx = (s.l + s.r) / 2, tcx = (t.l + t.r) / 2;
      let x1, y1, x2, y2, d;
      if (Math.abs(scx - tcx) < s.w / 2) {{
        x1 = scx; x2 = tcx;
        if (t.t >= s.b) {{ y1 = s.b; y2 = t.t; }} else {{ y1 = s.t; y2 = t.b; }}
        const k = Math.max(20, Math.abs(y2 - y1) / 2) * Math.sign(y2 - y1 || 1);
        d = `M${{x1}},${{y1}} C${{x1}},${{y1 + k}} ${{x2}},${{y2 - k}} ${{x2}},${{y2}}`;
      }} else {{
        const fwd = tcx > scx;
        x1 = fwd ? s.r : s.l; x2 = fwd ? t.l : t.r; y1 = s.t + Math.min(18, s.h / 2); y2 = t.t + Math.min(18, t.h / 2);
        const k = Math.max(30, Math.abs(x2 - x1) / 2) * (fwd ? 1 : -1);
        d = `M${{x1}},${{y1}} C${{x1 + k}},${{y1}} ${{x2 - k}},${{y2}} ${{x2}},${{y2}}`;
      }}
      const p = document.createElementNS(NS, 'path');
      p.setAttribute('d', d); p.setAttribute('class', 'l-' + L.type);
      if (L.type !== 'artefact') p.setAttribute('marker-end', `url(#ar-${{L.type}})`);
      p.dataset.from = L.from; p.dataset.to = L.to; svg.appendChild(p);
      if (L.label) {{
        const tx = document.createElementNS(NS, 'text');
        tx.setAttribute('x', (x1 + x2) / 2); tx.setAttribute('y', (y1 + y2) / 2 - 3); tx.setAttribute('text-anchor', 'middle');
        tx.textContent = L.label; tx.dataset.from = L.from; tx.dataset.to = L.to; svg.appendChild(tx);
      }}
    }});
    applyFilters();
  }}
  let pinned = null;
  function trace(id) {{
    board.classList.toggle('tracing', !!id);
    board.querySelectorAll('.hl').forEach(n => n.classList.remove('hl'));
    if (!id) return;
    const ids = new Set([id]);
    svg.querySelectorAll('path, text').forEach(n => {{
      if (n.dataset.from === id || n.dataset.to === id) {{ n.classList.add('hl'); ids.add(n.dataset.from); ids.add(n.dataset.to); }}
    }});
    ids.forEach(i => {{ const e = el(i); if (e) e.classList.add('hl'); }});
  }}
  board.querySelectorAll('.card').forEach(c => {{
    c.addEventListener('mouseenter', () => {{ if (!pinned) trace(c.dataset.id); }});
    c.addEventListener('mouseleave', () => {{ if (!pinned) trace(null); }});
    c.addEventListener('click', () => {{ pinned = pinned === c.dataset.id ? null : c.dataset.id; trace(pinned); }});
    c.addEventListener('keydown', e => {{ if (e.key === 'Enter' || e.key === ' ') {{ e.preventDefault(); c.click(); }} }});
  }});
  const fRel = document.getElementById('f-rel'), fVar = document.getElementById('f-var');
  function applyFilters() {{
    const rel = fRel ? +fRel.value : 9, v = fVar ? fVar.value : '';
    const dimmed = new Set();
    board.querySelectorAll('.card').forEach(c => {{
      const vars = (c.dataset.variant || '').split(';').map(s => s.trim()).filter(Boolean);
      const off = (+c.dataset.rel > rel) || (v && vars.length && !vars.includes(v));
      c.classList.toggle('dim', !!off); if (off) dimmed.add(c.dataset.id);
    }});
    svg.querySelectorAll('path, text').forEach(n => {{ if (n.dataset.from) n.classList.toggle('dimlink', dimmed.has(n.dataset.from) || dimmed.has(n.dataset.to)); }});
  }}
  if (fRel) fRel.addEventListener('change', applyFilters);
  if (fVar) fVar.addEventListener('change', applyFilters);
  document.getElementById('f-links').addEventListener('change', e => {{ svg.hidden = !e.target.checked; }});
  document.getElementById('f-spot').addEventListener('change', e => board.classList.toggle('spotlight', e.target.checked));
  let tm; window.addEventListener('resize', () => {{ clearTimeout(tm); tm = setTimeout(draw, 120); }});
  draw();
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(draw);
}})();
</script>
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("frame")
    ap.add_argument("cards")
    ap.add_argument("-o", "--out", required=True)
    a = ap.parse_args()
    frame = bp.load_frame(a.frame)
    cards, missing = bp.load_cards(a.cards)
    if missing:
        sys.exit(f"Card table is missing required columns: {', '.join(missing)}")
    with open(a.out, "w", encoding="utf-8") as f:
        f.write(page(frame, cards))
    print(f"Wrote {a.out} ({len(cards)} cards)")


if __name__ == "__main__":
    main()
