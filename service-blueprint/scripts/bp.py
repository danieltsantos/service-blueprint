# service-blueprint skill. Copyright 2026 Daniel Santos (danieltsantos.com). CC BY-NC 4.0, see LICENSE.txt.
"""Shared loading, parsing and checking for service blueprint frame + card files.

The formats are defined in references/notation.md. Other scripts import this module.
"""
import csv
import re
import sys
from collections import defaultdict

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("PyYAML is needed to read the frame file (pip install pyyaml).")

COLUMNS = ["id", "phase", "step", "lane", "type", "title", "body", "basis", "source",
           "owner", "cx_status", "release", "variant", "exc_status", "cx_risk",
           "trigger", "metric", "links"]
REQUIRED = ["id", "phase", "step", "lane", "type", "title", "basis"]
TYPES = {"start", "end", "task", "system", "gate", "message", "agent", "exception",
         "question", "decision", "gap", "friction", "idea", "moment", "evidence", "artefact", "policy"}
STICKIES = {"question", "decision", "gap", "friction", "idea", "moment"}
NO_LINK_NEEDED = STICKIES | {"start", "end", "evidence", "artefact", "exception", "policy"}
# Cards that can be the customer's touchpoint in a step (classic rule: one touchpoint per service moment).
TOUCHPOINT_TYPES = {"task", "system", "gate", "message", "agent"}
BASIS = {"evidence", "decided", "proposed", "assumption", "tbc", "gap"}
UNVERIFIED = {"proposed", "assumption", "tbc", "gap"}
RELEASES = {"", "R1", "R2", "R3", "RX", "TBC"}
EXC_STATUS = {"open", "workaround", "risk", "decided"}
LINK_TYPES = {"action", "system", "message", "artefact"}
ZONES = ["evidence", "customer", "frontstage", "backstage", "support", "artefacts", "exceptions"]
LINES = ["interaction", "visibility", "internal"]
BELOW_INTERACTION = {"frontstage", "backstage", "support"}
BELOW_VISIBILITY = {"backstage", "support"}


def load_frame(path):
    with open(path, encoding="utf-8") as f:
        frame = yaml.safe_load(f) or {}
    frame.setdefault("phases", [])
    frame.setdefault("lanes", [])
    frame.setdefault("sources", [])
    frame.setdefault("status_models", [])
    frame.setdefault("header", [])
    for p in frame["phases"]:
        p["id"] = str(p.get("id", "")).strip()
    return frame


def load_cards(path):
    """Return (cards, missing_columns). Cards are dicts with every column present."""
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = [h.strip() for h in (reader.fieldnames or [])]
        missing = [c for c in REQUIRED if c not in header]
        cards = []
        for i, row in enumerate(reader, start=2):
            card = {c: (row.get(c) or "").strip() for c in COLUMNS}
            if not any(card.values()):
                continue
            card["_row"] = i
            card["release"] = card["release"].upper()
            card["exc_status"] = card["exc_status"].lower()
            card["basis"] = card["basis"].lower()
            card["type"] = card["type"].lower()
            try:
                card["_step"] = int(float(card["step"] or 1))
            except ValueError:
                card["_step"] = 1
            cards.append(card)
    return cards, missing


def parse_links(s):
    """'3.1>action:YES; 2.4>system' -> [('3.1','action','YES'), ('2.4','system','')]."""
    out = []
    for item in (s or "").split(";"):
        item = item.strip()
        if not item:
            continue
        if ">" in item:
            target, rest = item.split(">", 1)
            if ":" in rest:
                ltype, label = rest.split(":", 1)
            else:
                ltype, label = rest, ""
        elif ":" in item:
            target, label = item.split(":", 1)
            ltype = "action"
        else:
            target, ltype, label = item, "action", ""
        out.append((target.strip(), (ltype.strip() or "action").lower(), label.strip()))
    return out


def lane_list(frame):
    """Lanes in order, each with index, plus the index of the lane each line sits above."""
    lanes, lines = [], {}
    for entry in frame["lanes"]:
        if "line" in entry:
            lines[str(entry["line"]).lower()] = len(lanes)
        else:
            lane = dict(entry)
            lane["id"] = str(lane.get("id", "")).strip()
            lane["zone"] = str(lane.get("zone", "")).lower()
            lane["_idx"] = len(lanes)
            lanes.append(lane)
    return lanes, lines


def phase_columns(frame, cards):
    """phase id -> (first global column, number of columns)."""
    steps = defaultdict(int)
    for c in cards:
        steps[c["phase"]] = max(steps[c["phase"]], c["_step"])
    cols, start = {}, 0
    for p in frame["phases"]:
        n = max(1, steps.get(p["id"], 1))
        cols[p["id"]] = (start, n)
        start += n
    return cols


def state_patterns(frame):
    """Compile status model states; '{date}' style placeholders match anything."""
    pats = []
    for model in frame["status_models"]:
        for st in model.get("states", []):
            name = str(st.get("name", "")).strip()
            rx = re.escape(name)
            rx = re.sub(r"\\\{[^}]*\\\}", ".+", rx)
            pats.append((model.get("name", ""), name, re.compile("^" + rx + "$", re.I)))
    return pats


def check(frame, cards, missing_columns=()):
    """Return (format_errors, quality) where quality is a list of
    {'id','name','passed','details':[...]} following SKILL.md section 12."""
    errors = []
    if missing_columns:
        errors.append(f"Card table is missing required columns: {', '.join(missing_columns)}")
    lanes, lines = lane_list(frame)
    lane_by_id = {l["id"]: l for l in lanes}
    phase_ids = [p["id"] for p in frame["phases"]]
    source_ids = {str(s.get("id", "")).strip() for s in frame["sources"]}

    by_id, dupes = {}, []
    for c in cards:
        if c["id"] in by_id:
            dupes.append(c["id"])
        by_id[c["id"]] = c
    if dupes:
        errors.append(f"Duplicate card IDs: {', '.join(sorted(set(dupes)))}")

    for c in cards:
        where = f"Card {c['id'] or '(no id)'} (row {c['_row']})"
        for col in REQUIRED:
            if not c[col]:
                errors.append(f"{where}: empty '{col}'")
        if c["phase"] and c["phase"] not in phase_ids:
            errors.append(f"{where}: phase '{c['phase']}' is not in the frame")
        if c["lane"] and c["lane"] not in lane_by_id:
            errors.append(f"{where}: lane '{c['lane']}' is not in the frame")
        if c["type"] and c["type"] not in TYPES:
            errors.append(f"{where}: unknown type '{c['type']}'")
        if c["basis"] and c["basis"] not in BASIS:
            errors.append(f"{where}: unknown basis '{c['basis']}'")
        if c["release"] not in RELEASES:
            errors.append(f"{where}: unknown release '{c['release']}'")
        if c["exc_status"] and c["exc_status"] not in EXC_STATUS:
            errors.append(f"{where}: unknown exc_status '{c['exc_status']}'")
        for target, ltype, _ in parse_links(c["links"]):
            if target not in by_id:
                errors.append(f"{where}: links to missing card '{target}'")
            if ltype not in LINK_TYPES:
                errors.append(f"{where}: unknown link type '{ltype}'")

    # graph
    out_links = defaultdict(list)
    in_links = defaultdict(list)
    for c in cards:
        for target, ltype, label in parse_links(c["links"]):
            if target in by_id:
                out_links[c["id"]].append((target, ltype, label))
                in_links[target].append((c["id"], ltype, label))

    def zone(cid):
        lane = lane_by_id.get(by_id[cid]["lane"]) if cid in by_id else None
        return lane["zone"] if lane else ""

    def neighbours(cid):
        return {t for t, _, _ in out_links[cid]} | {s for s, _, _ in in_links[cid]}

    quality = []

    def add(qid, name, details):
        quality.append({"id": qid, "name": name, "passed": not details, "details": details})

    # Q1 tracing
    d = []
    for c in cards:
        if zone(c["id"]) == "customer" and c["type"] in {"task", "gate"}:
            seen, frontier, ok = {c["id"]}, {c["id"]}, False
            for _ in range(2):
                nxt = set()
                for n in frontier:
                    nxt |= neighbours(n) - seen
                if any(zone(n) in BELOW_INTERACTION for n in nxt):
                    ok = True
                    break
                seen |= nxt
                frontier = nxt
            if not ok:
                d.append(f"{c['id']} '{c['title']}' has no trace below the line of interaction within two links")
    for pid in phase_ids:
        if not any(c["phase"] == pid and zone(c["id"]) in BELOW_VISIBILITY for c in cards):
            d.append(f"Phase {pid} has no card below the line of visibility")
    add("Q1", "Customer actions traced below the lines", d)

    # Q2 gates
    d = []
    for c in cards:
        if c["type"] == "gate":
            # Links to policies or documents are references, not branches.
            outs = [l for l in out_links[c["id"]] if l[1] != "artefact"]
            if len(outs) < 2:
                d.append(f"Gate {c['id']} has {len(outs)} branch(es); needs at least 2")
            unlabelled = [t for t, _, lab in outs if not lab]
            if unlabelled:
                d.append(f"Gate {c['id']} has unlabelled branch(es) to {', '.join(unlabelled)}")
    add("Q2", "Gates have labelled branches", d)

    # Q3 statuses
    d = []
    pats = state_patterns(frame)
    set_states = set()
    for c in cards:
        if c["cx_status"]:
            hits = [(m, n) for m, n, rx in pats if rx.match(c["cx_status"])]
            if not hits:
                d.append(f"{c['id']} sets status '{c['cx_status']}', which is in no status model")
            set_states |= set(hits)
    for m, n, _ in pats:
        if (m, n) not in set_states:
            d.append(f"Status '{n}' ({m}) is never set by a card")
    add("Q3", "Customer-visible statuses match the status models", d)

    # Q4 exceptions
    d = []
    for c in cards:
        if c["type"] == "exception":
            gaps = [f for f in ("exc_status", "owner", "cx_risk") if not c[f]]
            if gaps:
                d.append(f"Exception {c['id']} is missing {', '.join(gaps)}")
    add("Q4", "Exceptions have status, owner and CX risk", d)

    # Q5 basis and sources
    d = []
    for c in cards:
        srcs = [s.strip() for s in c["source"].split(";") if s.strip()]
        unknown = [s for s in srcs if s not in source_ids]
        if unknown:
            d.append(f"{c['id']} cites unknown source(s) {', '.join(unknown)}")
        if c["basis"] == "evidence" and not srcs:
            d.append(f"{c['id']} is marked evidence but cites no source")
        if c["basis"] == "decided" and not srcs and not c["owner"]:
            d.append(f"{c['id']} is marked decided but names no source or owner")
    add("Q5", "Every card has a basis and evidence cites a real source", d)

    # Q6 orphans
    d = []
    for c in cards:
        if c["type"] not in NO_LINK_NEEDED and not out_links[c["id"]] and not in_links[c["id"]]:
            d.append(f"{c['id']} '{c['title']}' has no links in or out")
    add("Q6", "No orphan cards", d)

    # Q7 lines and lane zones
    d = []
    for ln in LINES:
        if ln not in lines:
            d.append(f"Line of {ln} is missing from the frame")
    if all(ln in lines for ln in LINES):
        li, lv, lint = lines["interaction"], lines["visibility"], lines["internal"]
        if not li <= lv <= lint:
            d.append("Lines are out of order (interaction, visibility, internal)")
        for lane in lanes:
            z, i = lane["zone"], lane["_idx"]
            if z not in ZONES:
                d.append(f"Lane {lane['id']} has unknown zone '{z}'")
            elif z == "customer" and i >= li:
                d.append(f"Customer lane {lane['id']} sits below the line of interaction")
            elif z == "frontstage" and not (li <= i < lv):
                d.append(f"Frontstage lane {lane['id']} is not between the lines of interaction and visibility")
            elif z == "backstage" and not (lv <= i < lint):
                d.append(f"Backstage lane {lane['id']} is not between the lines of visibility and internal interaction")
            elif z == "support" and i < lint:
                d.append(f"Support lane {lane['id']} sits above the line of internal interaction")
    add("Q7", "Lines present and lanes on the right side of them", d)

    # Q8 open decisions and agent cards
    d = []
    for c in cards:
        if c["basis"] == "tbc" and not c["title"].rstrip().endswith("?"):
            d.append(f"{c['id']} is tbc but its title is not a question")
        if c["type"] == "agent" and not (c["trigger"] and c["metric"]):
            d.append(f"Agent card {c['id']} is missing trigger or metric")
    if str(frame.get("state", "")).startswith("to-be") and not any(c["basis"] in {"tbc", "gap"} or c["type"] in {"question", "gap"} for c in cards):
        d.append("To-be blueprint has no open questions or gaps; check that open decisions were not made silently")
    add("Q8", "Open decisions visible; agent cards complete", d)

    # Q9 phase coverage
    d = []
    for pid in phase_ids:
        if not any(c["phase"] == pid for c in cards):
            d.append(f"Phase {pid} has no cards")
    if not any(c["type"] == "start" for c in cards):
        d.append("No start card")
    if not any(c["type"] == "end" for c in cards):
        d.append("No end card")
    add("Q9", "Phases cover scope from start to end", d)

    # Q10 one touchpoint per customer action
    d = []
    for c in cards:
        if zone(c["id"]) == "customer" and c["type"] == "task":
            tps = sorted({n for n in neighbours(c["id"])
                          if zone(n) in {"evidence", "frontstage"} and by_id[n]["type"] in TOUCHPOINT_TYPES
                          and by_id[n]["phase"] == c["phase"] and by_id[n]["_step"] == c["_step"]})
            if len(tps) > 1:
                d.append(f"{c['id']} '{c['title']}' uses {len(tps)} touchpoints in the same step ({', '.join(tps)}); split the step or keep one")
    add("Q10", "One touchpoint per customer action", d)

    return errors, quality


def decision_list(cards):
    """Cards that need a decision: open or unowned exceptions, tbc, gap, open questions."""
    out = []
    for c in cards:
        if c["type"] == "exception" and (c["exc_status"] == "open" or c["owner"].lower() in {"", "unassigned"}):
            out.append(("Exception", c))
        elif c["basis"] == "tbc" or c["type"] == "question":
            out.append(("Open question", c))
        elif c["basis"] == "gap" or c["type"] == "gap":
            out.append(("Gap", c))
    return out
