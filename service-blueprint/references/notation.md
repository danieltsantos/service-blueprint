# Notation and data formats

Read this before writing cards. It defines the frame file, the card table, the card types, connectors, IDs, tags and the Portuguese glossary. The scripts in `scripts/` read exactly these formats.

## Contents

1. Frame file (`<slug>-frame.yaml`)
2. Card table (`<slug>-cards.csv`)
3. Card types
4. Connectors and the `links` column
5. IDs
6. Tags: release, variant, exception status
7. Optional emoji prefixes
8. AI agent cards
9. Header block
10. European Portuguese glossary

---

## 1. Frame file

YAML. Everything that is not a card lives here. The values below come from the invented example in `assets/example-frame.yaml`, which has the full file.

```yaml
title: Sample broadband blueprint
deliverable: L0 service blueprint for installing broadband at a small business site
owner: unassigned               # a person the user named; otherwise "unassigned"
last_updated: 2026-11-07
state: to-be                    # as-is | to-be | as-is+to-be
layer: L0                       # L0 end-to-end | L1 stage or sub-journey | L2 one touchpoint or vertical
parent:                         # L1 and L2 only: the blueprint this one expands
  title: ""                     #   e.g. "Broadband installation L0"
  expands: ""                   #   parent card IDs, e.g. "2.1-2.5"
status: WIP                     # WIP | review | agreed
language: en                    # en | pt-PT; also sets the language of the rendered page's interface and credit
lane_policy: >                  # one line on how third-party and mixed-visibility actors are placed
  The contractor's technician meets the customer on site, so sits in a frontstage lane.
attribution:                    # optional; only when the user asks for a credit or licence on the page
  author: ""                    #   the user's name, as they give it
  url: ""
  year: 2026
  licence: ""                   #   e.g. "CC BY-NC 4.0"
  licence_url: ""
  note: ""                      #   optional short line

header:                         # boxes in the header block, in order
  - heading: Executive description
    items: ["Let small businesses order broadband online and get a working line on the first visit."]
  - heading: Core user need
    items: ["I need to know when my line will work, so I can plan around the downtime."]
  - heading: Metrics to move
    items: ["% of installs working after the first visit"]

sources:
  - {id: S1, name: "Order flow specification", type: process, date: 2026-09, link: ""}
  - {id: S2, name: "Customer interviews, round 1", type: primary, date: 2026-10, link: ""}
  - {id: S3, name: "Kick-off summary made with an AI assistant", type: ai-synthesis, date: 2026-10, link: ""}

phases:
  - id: 2
    name: Pre-install checks
    subtitle: Line test and visit confirmation
    cx: Visit confirmed
    sla: Confirmation at least 48 hours before the visit

lanes:                          # top to bottom; `line` entries draw the three lines
  - {id: touch, name: "Customer messages", zone: evidence}
  - {id: customer, name: "Customer", zone: customer}
  - {line: interaction}
  - {id: web, name: "Website and app", note: "What the customer sees", zone: frontstage}
  - {id: tech, name: "Field technician", note: "Contractor, on site", zone: frontstage}
  - {line: visibility}
  - {id: oms, name: "Order system", zone: backstage}
  - {line: internal}
  - {id: netops, name: "Network operations", zone: support}
  - {id: dispatch, name: "Contractor dispatch", zone: support}
  - {id: docs, name: "Supporting documents", zone: artefacts}
  - {id: exc, name: "Exceptions & edge cases", zone: exceptions}

status_models:
  - name: Order status
    states:
      - {name: "Order received", set_by: "order created"}
      - {name: "Visit booked for {date}", set_by: "technician slot reserved"}
```

`zone` values: `evidence`, `customer`, `frontstage`, `backstage`, `support`, `artefacts`, `exceptions`. The checker uses zones to test tracing, so set them even when lane names are unusual.

## 2. Card table

CSV, UTF-8, one row per card. Leave cells empty when they do not apply. Quote cells that contain commas.

| Column | Required | Values |
|---|---|---|
| `id` | yes | See section 5 |
| `phase` | yes | A phase `id` from the frame |
| `step` | yes | Integer column inside the phase, from 1. Cards with the same phase and step line up vertically, so give a customer action and the backstage work it triggers the same or adjacent steps. |
| `lane` | yes | A lane `id` from the frame |
| `type` | yes | See section 3 |
| `title` | yes | Short. Gates and `tbc` cards are questions. |
| `body` | no | One to three short lines |
| `basis` | yes | `evidence`, `decided`, `proposed`, `assumption`, `tbc`, `gap` |
| `source` | if evidence | Source IDs, separated by `;` |
| `owner` | exceptions | Team or person named in the inputs, or `unassigned` |
| `cx_status` | no | The customer-visible status this card sets. Must match a state in a status model. |
| `release` | no | Empty means first release. `R2`, `R3`, `RX`, `TBC` |
| `variant` | no | Variant tags separated by `;`, e.g. `Fibre;Copper` or `North;South` |
| `exc_status` | exceptions | `open`, `workaround`, `risk`, `decided` |
| `cx_risk` | exceptions | What the customer suffers if this goes wrong |
| `trigger` | agent cards | What invokes the agent |
| `metric` | agent cards | What you would measure here |
| `links` | no | Outgoing connectors, see section 4 |

## 3. Card types

| type | Use for | Default look |
|---|---|---|
| `start` / `end` | Start trigger, end condition | Black circle |
| `task` | An action by a person (customer, staff, contractor) | White box. Dashed border when `basis` is `tbc`. |
| `system` | An automated action by a system | Light blue box |
| `gate` | A decision with labelled branches | Yellow diamond or box with a diamond marker |
| `message` | Email, notification, letter, SMS sent to the customer | Grey box, usually in the touchpoints lane |
| `agent` | An AI agent action | Violet box |
| `exception` | An exception or edge case | Red (open) or orange (workaround, risk) box |
| `question` | Open question sticky | Yellow sticky |
| `decision` | Decision sticky ("DECIDED: ...") | Green sticky |
| `gap` | Gap sticky ("GAP: ...") | Pink sticky |
| `friction` | Known friction, usually from research | Orange sticky |
| `idea` | Improvement idea or "ideal CX" note | Light green sticky |
| `evidence` | A research finding attached to a step | Teal box with source |
| `artefact` | A linked document, design, ticket, comms asset | Box with link, in the artefacts lane |

Stickies (`question` to `idea`) do not need links. Every other type except `start`, `end`, `evidence` and `artefact` should have at least one link in or out.

## 4. Connectors and `links`

Write outgoing links in the source card's `links` cell:

```
target>type:label; target>type:label
```

- `target`: another card's `id`
- `type`: `action` (solid arrow, direct sequence), `system` (dashed arrow, system-to-system or indirect dependency), `message` (blue dashed arrow, message flow to the customer), `artefact` (dotted line to a supporting document). Default `action`.
- `label`: optional. Required on every branch out of a gate. Use `handoff` for an agent passing work to a human.

Examples: `2.2>system`, `3.3>action:YES; 2.4>action:NO`, `2.5>message:notifies`, `2.D1>artefact`.

## 5. IDs

- Cards on the main flow: `phase.step`, with a sub-number for siblings: `2.1`, `2.2`, `2.2.1`, `2.2.2`. IDs need not match the `step` column exactly, but keep them in reading order.
- Exceptions: `phase.Xn`, e.g. `3.X1`.
- Stickies: `phase.Nn`, e.g. `4.N2`.
- Artefacts: `phase.Dn`, e.g. `2.D1`.
- Start and end: `start`, `end`, or `1.START`, `6.END`.

IDs never change once a board is shared, because people quote them in tickets and meetings. Add new cards with new numbers rather than renumbering.

## 6. Tags

**Release** (to-be only): empty = first release; `R2`; `R3`; `RX` = later, release not decided; `TBC` = the decision itself is open.

**Variant**: tags for countries, tiers, channels or segments that see a different version of the step. Tag the differing cards; branch the flow only where the sequence differs.

**Exception status**: `open` (unowned, unresolved), `workaround` (handled manually or temporarily), `risk` (known risk, partly mitigated or hypothetical), `decided` (resolved, kept for the record).

## 7. Optional emoji prefixes

Use them when the user's boards do, at the start of the title:

👀 customer sees or checks · ✉️ message sent · ⚙️ system action · 📦 physical item · 🛟 contacts care · ☎️ phone call · 💶 money moves · 🤖 AI agent

## 8. AI agent cards

An agent action sits in `ai-front` (in view of the customer) or `ai-ops` (out of sight). Example rows:

```csv
id,phase,step,lane,type,title,body,basis,source,owner,cx_status,release,variant,exc_status,cx_risk,trigger,metric,links
3.4,3,4,ai-front,agent,🤖 Proposes a fix,Answers from the help centre and the account's plan. Shows sources.,proposed,,,,,,,,User asks a billing question in chat,Resolved without handoff,3.5>system
3.5,3,4,ai-ops,agent,🤖 Confidence check,Below threshold or policy topic → hand to a human with the chat summary.,proposed,,,,,,,,Answer drafted,Handoff rate,3.6>action:handoff
3.6,3,5,care,task,Care agent picks up the chat,Reads the summary and replies. Queue SLA not defined yet.,assumption,,,,,,,,,,
3.X1,3,5,exc,exception,Handoff loses context,Summary missing or wrong. Customer repeats themselves.,assumption,,unassigned,,,,open,Customer repeats the problem and loses trust,,,
```

## 9. Header block

Default boxes, left to right: executive description, journey type and layer (state, layer, status), project links and owner, main goals, core user need, key user stories, key delivery references, key design references, documents and sources, metrics to move. Drop boxes the inputs give nothing for, and say in your reply which ones you dropped. Header boxes are for the board's readers: never add a box of notes about your own work (what you could not read, your limits as a builder).

## 10. European Portuguese glossary

Use Portuguese as written in Portugal today, never Brazilian Portuguese. Vocabulary: "contacto", "equipa", "ecrã", "utilizador", "telemóvel", "registo". Spelling follows the current norm in Portugal (AO90): "interação", "exceção", "arquitetura", "ação". Use the "tu/vocês" or formal register the user's own text uses.

| English | pt-PT (AO90) |
|---|---|
| Service blueprint | Blueprint de serviço |
| Line of interaction | Linha de interação |
| Line of visibility | Linha de visibilidade |
| Line of internal interaction | Linha de interação interna |
| Frontstage / backstage | Frontstage / backstage (keep the English terms unless the user prefers "palco / bastidores") |
| Support processes | Processos de suporte |
| Touchpoints | Pontos de contacto |
| Customer | Cliente |
| Phase | Fase |
| Gate | Ponto de decisão |
| Exception / edge case | Exceção / caso-limite |
| Owner | Responsável |
| CX risk | Risco para o cliente |
| Open question | Questão em aberto |
| Assumption | Pressuposto |
| Evidence | Evidência |
| Decided / proposed | Decidido / proposto |
| Gap | Lacuna |
| Status model | Modelo de estados |
| Supporting documents | Documentos de suporte |
| Release | Release (keep R1, R2, RX) |
