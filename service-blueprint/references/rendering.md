# Rendering and reading blueprints

The card table and frame file are the source of truth. Every renderer below draws from them, so edit the table and re-render rather than editing a board by hand and losing the table.

## Contents

1. Choosing a target
2. HTML page
3. Spreadsheet
4. FigJam
5. Miro
6. Reading an existing blueprint (critique mode)

---

## 1. Choosing a target

| Target | Token cost beyond the table | Best for | Status in this skill |
|---|---|---|---|
| HTML page | Almost none: a script writes the page and it is published by file path | Drafts, reviews, sharing a link, phones | Tested |
| Spreadsheet | None | Editing cards in bulk, importing elsewhere | Tested (it is the CSV) |
| FigJam | High: the whole layout and drawing code go through the tool call, plus the Figma skills | Team workshops, the user's usual board | Not yet tested end to end |
| Miro | High: the whole board goes through the tool call as SVG | Teams that live in Miro | Not yet tested end to end |

For a 50-card blueprint the frame and table are about 11 KB, and the layout JSON for a board renderer about 21 KB before any drawing code. Render to a board once the content has settled; use the HTML page for the review rounds before that.

## 2. HTML page

```bash
python scripts/render_html.py <slug>-frame.yaml <slug>-cards.csv -o <slug>.html
```

Then publish `<slug>.html` with the Artifact tool (`icon`: `diagram`; `description`: one sentence naming the service and state). Republish the same path after each revision so the link stays the same.

The page has the header block, legend, phase timeline, lanes and lines, cards and connectors. Viewers can filter by release and variant, spotlight unverified cards, and tap a card to trace its connections. Below the board it lists what needs a decision, the quality checks, the status models and the sources. Do not hand-edit the generated HTML; change the data and re-render.

The page follows the Artifact page contract already. If the user wants a different look, change the template in `render_html.py` once, not per blueprint.

## 3. Spreadsheet

The CSV opens in any spreadsheet. If the session lists a Sheets artifact type, create one from the card table so the user can edit it in place. If the user asks for an .xlsx, use the xlsx skill: one sheet for cards, one for phases and lanes, one for sources, first row frozen, `basis` and `type` as dropdowns. Read edits back into the CSV before re-rendering.

## 4. FigJam

1. **Ask first** unless the user asked for FigJam in this request: drawing writes to their Figma account. If they give a FigJam link, use its file key (`figma.com/board/<fileKey>/...`).
2. **Load the Figma guidance** before any `use_figma` call: the `figma-use` and `figma-use-figjam` skills (or the `skill://figma/figma-use/SKILL.md` and `skill://figma/figma-use-figjam/SKILL.md` resources through `get_figma_skill`). For a new file, load `figma-create-new-file` and call `create_new_file` for a FigJam board. Then call `create_session` with the file key and reuse its `sessionId`.
3. **Export the layout**:
   ```bash
   python scripts/export_layout.py <frame> <cards> -o layout.json            # whole board
   python scripts/export_layout.py <frame> <cards> -o layout-p2.json --phase 2   # one phase
   ```
   `use_figma` accepts at most 50,000 characters of code per call. Above roughly 40 cards, send one phase per call.
4. **Draw in this order**, one call each:
   - Scaffold: lane bands as rectangles from `lanes`, lane labels, the three lines as dashed lines at `lines[].y`, phase headers from `phases`.
   - Cards, per phase: a shape with text per card at its `x`, `y`, `w`, filled with `fill` and stroked with `stroke`; sticky notes for `question`, `decision`, `gap`, `friction` and `idea`. Name every node with the card ID so later calls can find it.
   - Connectors, per phase: find both nodes by name and connect them, using `colour`, `dash` and `label` from `links`.
   Paste the layout JSON into the code as a constant and loop over it. Never retype card text by hand inside drawing code: that is where content drifts from the table.
5. **Check once** with `get_screenshot` on the board. Fix what is visibly wrong in one pass. Card heights in the layout are estimates; let text auto-size and grow lane bands if cards overflow.

Do not use `generate_diagram` (Mermaid) for the full blueprint: it cannot hold cards to lanes and columns. It works well for a status model (`stateDiagram-v2`) or a quick flow sketch of one phase.

## 5. Miro

1. **Ask first** unless the user asked for Miro in this request: creating a board cannot be undone.
2. Load `canvas_get_canvas_composer_skill`, then `canvas_load_format_skill` with `format_name: diagramming`, `notation: free_form`, `renderer: native`.
3. Export the layout as for FigJam and translate it into Canvas Composer SVG: one rectangle per lane band, shapes with text for cards, sticky notes for note types, connectors for links. `canvas_create_from_svg` accepts up to 200,000 characters per call; send one phase per call for large boards.
4. Check once with `canvas_read_as_svg` or `board_preview_read`.

## 6. Reading an existing blueprint (critique mode)

- **PDF or large image**: text extraction alone loses which lane and phase a card sits in. Rasterise the page at about 300 dpi and read crops: the lane labels column, the legend, the header row, then each phase. Use the extracted text to get exact wording.
- **FigJam**: `get_figjam` for content and `get_screenshot` for layout, after `create_session`.
- **Miro**: `canvas_read_as_svg` for content, `board_preview_read` for a picture.

Record the author's own legend before judging anything. A blueprint that departs from these conventions on purpose is not wrong; judge it against its own legend first, then say where these conventions would change what a reader understands.
