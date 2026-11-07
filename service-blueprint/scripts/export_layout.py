#!/usr/bin/env python3
# service-blueprint skill. Copyright 2026 Daniel Santos (danieltsantos.com). CC BY-NC 4.0, see LICENSE.txt.
"""Export a laid-out blueprint as compact JSON for board renderers (FigJam via use_figma, Miro via SVG).

Usage:
  python export_layout.py <frame.yaml> <cards.csv> -o <layout.json> [--phase N]

Positions are absolute board coordinates in px. Card heights are estimates from text length;
board renderers should let text auto-size and treat lane heights as minimums.
--phase limits the output to one phase, for sending a large board in several calls.
"""
import argparse
import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bp  # noqa: E402

LABEL_W, COL_W, CARD_W, GAP, PAD = 240, 280, 240, 16, 20
PHASE_H, TIMELINE_H, LINE_H = 90, 70, 30
ZONE_FILL = {"evidence": "#E7E0CF", "customer": "#1D2421", "frontstage": "#D9E6EF", "backstage": "#E6DFEE",
             "support": "#DFE8DF", "artefacts": "#E4EFE2", "exceptions": "#F6E4D6"}
TYPE_STYLE = {  # fill, stroke
    "start": ("#1D2421", "#1D2421"), "end": ("#1D2421", "#1D2421"), "task": ("#FFFFFF", "#9AA29D"),
    "system": ("#DCEBF7", "#5F93BD"), "gate": ("#FFF4C7", "#C9A227"), "message": ("#ECEEED", "#8B928E"),
    "agent": ("#EBE3F8", "#7A5BBD"), "exception": ("#FBE1DF", "#C2413B"), "question": ("#FFF2A8", "#FFF2A8"),
    "decision": ("#D4F0CF", "#D4F0CF"), "gap": ("#FBD9E6", "#FBD9E6"), "friction": ("#FFDCBC", "#FFDCBC"),
    "idea": ("#E3F4D6", "#E3F4D6"), "moment": ("#FFE0F0", "#FFE0F0"), "evidence": ("#D7EFEB", "#2D8A7D"),
    "policy": ("#EEF0F6", "#5A6487"), "artefact": ("#FFFFFF", "#9AA29D"),
}
LINK_STYLE = {"action": ("#2B322E", "solid"), "system": ("#7C8580", "dashed"),
              "message": ("#2A6FB0", "dashed"), "artefact": ("#9AA29D", "dotted")}
LINE_COLOUR = {"interaction": "#2E8B57", "visibility": "#2A6FB0", "internal": "#1B9AA8"}


def card_text(c):
    bits = [c["id"] + (f"  [{c['release']}]" if c["release"] else "") + (f"  ({c['basis']})" if c["basis"] in bp.UNVERIFIED else ""),
            c["title"]]
    if c["body"]:
        bits.append(c["body"])
    for k, label in (("cx_status", "CX status"), ("trigger", "Trigger"), ("metric", "Metric"),
                     ("owner", "Owner"), ("cx_risk", "CX risk"), ("variant", "Variant"), ("source", "Source")):
        if c[k] and not (c["type"] in {"start", "end"} and k == "source"):
            bits.append(f"{label}: {c[k]}")
    return "\n".join(bits)


def est_height(text):
    lines = sum(max(1, math.ceil(len(part) / 34)) for part in text.split("\n"))
    return 24 + 17 * lines


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("frame")
    ap.add_argument("cards")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--phase")
    a = ap.parse_args()
    frame = bp.load_frame(a.frame)
    cards, missing = bp.load_cards(a.cards)
    if missing:
        sys.exit(f"Card table is missing required columns: {', '.join(missing)}")
    lanes, lines = bp.lane_list(frame)
    cols = bp.phase_columns(frame, cards)
    ncols = sum(n for _, n in cols.values()) or 1

    cells = defaultdict(list)
    for c in cards:
        if c["phase"] in cols:
            start, n = cols[c["phase"]]
            c["_col"] = start + min(max(c["_step"], 1), n) - 1
            c["_text"] = card_text(c)
            c["_h"] = est_height(c["_text"])
            cells[(c["lane"], c["_col"])].append(c)

    out = {"title": frame.get("title", ""), "deliverable": frame.get("deliverable", ""),
           "meta": {k: frame.get(k) for k in ("owner", "last_updated", "state", "layer", "status") if frame.get(k)},
           "header": frame["header"], "phases": [], "lanes": [], "lines": [], "cards": [], "links": []}
    for p in frame["phases"]:
        start, n = cols[p["id"]]
        out["phases"].append({"id": p["id"], "name": p.get("name", ""), "subtitle": p.get("subtitle", ""),
                              "cx": p.get("cx", ""), "sla": p.get("sla", "") or "TBC",
                              "x": LABEL_W + start * COL_W, "w": n * COL_W, "y": 0, "h": PHASE_H + TIMELINE_H})
    y = PHASE_H + TIMELINE_H
    for lane in lanes:
        for kind, idx in lines.items():
            if idx == lane["_idx"]:
                out["lines"].append({"kind": kind, "y": y + LINE_H // 2, "colour": LINE_COLOUR.get(kind, "#555555")})
                y += LINE_H
        h = 100
        for col in range(ncols):
            stack = cells.get((lane["id"], col), [])
            if stack:
                h = max(h, 2 * PAD + sum(c["_h"] for c in stack) + GAP * (len(stack) - 1))
        out["lanes"].append({"id": lane["id"], "name": lane.get("name", lane["id"]), "note": lane.get("note", ""),
                             "zone": lane["zone"], "y": y, "h": h, "fill": ZONE_FILL.get(lane["zone"], "#EEEEEE")})
        for col in range(ncols):
            cy = y + PAD
            for c in cells.get((lane["id"], col), []):
                fill, stroke = TYPE_STYLE.get(c["type"], ("#FFFFFF", "#9AA29D"))
                if c["type"] == "exception" and c["exc_status"] in {"workaround", "risk"}:
                    fill, stroke = "#FDEBD3", "#D07A1C"
                out["cards"].append({"id": c["id"], "phase": c["phase"], "type": c["type"], "basis": c["basis"],
                                     "text": c["_text"], "x": LABEL_W + col * COL_W + (COL_W - CARD_W) // 2, "y": cy,
                                     "w": CARD_W, "h": c["_h"], "fill": fill, "stroke": stroke,
                                     "dashed": c["basis"] == "tbc" and c["type"] in {"task", "system"}})
                cy += c["_h"] + GAP
        y += h
    for kind, idx in lines.items():
        if idx >= len(lanes):
            out["lines"].append({"kind": kind, "y": y + LINE_H // 2, "colour": LINE_COLOUR.get(kind, "#555555")})
            y += LINE_H
    for c in cards:
        for target, ltype, label in bp.parse_links(c["links"]):
            colour, dash = LINK_STYLE.get(ltype, LINK_STYLE["action"])
            out["links"].append({"from": c["id"], "to": target, "type": ltype, "label": label, "colour": colour, "dash": dash})
    out["board"] = {"width": LABEL_W + ncols * COL_W, "height": y}
    pt = str(frame.get("language", "en")).lower().startswith("pt")
    credit = ("Feito com o modelo service-blueprint de Daniel Santos \u00b7 Licença do modelo CC BY-NC 4.0" if pt
              else "Made with the service-blueprint template by Daniel Santos \u00b7 Template licence CC BY-NC 4.0")
    out["credit"] = {"text": credit,
                     "x": out["board"]["width"], "y": y + 24, "align": "right", "size": 11, "colour": "#8A928D"}

    if a.phase:
        keep = {c["id"] for c in out["cards"] if c["phase"] == str(a.phase)}
        out["cards"] = [c for c in out["cards"] if c["id"] in keep]
        out["links"] = [l for l in out["links"] if l["from"] in keep]
        out["phases"] = [p for p in out["phases"] if p["id"] == str(a.phase)]

    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"), default=str)
    print(f"Wrote {a.out}: {len(out['cards'])} cards, {len(out['links'])} links, board {out['board']['width']}x{out['board']['height']}px, "
          f"{os.path.getsize(a.out)} bytes")


if __name__ == "__main__":
    main()
