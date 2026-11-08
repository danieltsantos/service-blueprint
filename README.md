# Service Blueprint skill for Claude

A skill that teaches Claude to build service blueprints from a concept, from research, or from scratch. It comes with a full example so you can see the result before you install anything.

Beta · Licence [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) · By [Daniel Santos](https://danieltsantos.com)

**[See the example](https://danieltsantos.github.io/service-blueprint/)** · **[Exemplo em português](https://danieltsantos.github.io/service-blueprint/exemplo-pt.html)** · **[Download the skill](https://github.com/danieltsantos/service-blueprint/raw/main/service-blueprint.zip)**

---

## Before you start

- You need a Claude account. The free plan works.
- You need a computer, because you install the skill from the website or the desktop app.
- It takes about ten minutes.

## 1. Look at the examples

Open the [example](https://danieltsantos.github.io/service-blueprint/). It is an invented blueprint for installing broadband at a small shop.

There is also an [example in European Portuguese](https://danieltsantos.github.io/service-blueprint/exemplo-pt.html): visiting a Loja de Cidadão. Its rules and figures come from public sources; the shop, the person and the interviews are fictional, and the **Fonte pública** button fades the fiction. Its data files are in [`docs/exemplo-pt`](docs/exemplo-pt).

Try this:

- Tap a card to see where it comes from and where it leads.
- Switch the **Release** buttons on and off to see what ships in each release. The page says how many cards are showing.
- Tap **Spotlight unverified** to see what is still an assumption, and **Connectors** to hide the arrows.
- Scroll to the end. **Needs a decision** lists what the team still has to decide.

## 2. Install the skill

1. Download [service-blueprint.zip](https://github.com/danieltsantos/service-blueprint/raw/main/service-blueprint.zip). Do not unzip it.
2. In Claude, open **Settings**, then **Capabilities**. Turn on **Code execution and file creation**. The skill does not work without it.
3. Go to **Customize**, then **Skills**. Click **+**, then **Create skill**.
4. Choose **Upload a skill** and select the ZIP.
5. Check that **service-blueprint** appears in the list and is switched on.

Menu names can change between versions of Claude. If you can't find one, search Claude's help centre for "use skills in Claude".

## 3. Use the skill

You don't need to call it by name. Ask for a blueprint and Claude uses it. Always attach the files you mention.

| You have | Write something like |
|---|---|
| A concept or workshop notes | "Here are the notes from the workshop on the new booking service. Make a to-be L0 blueprint." |
| Interviews, journey maps or process docs | "I have two interviews and the current journey map. I need the as-is blueprint as a spreadsheet." |
| Someone else's blueprint | "Review this blueprint before I show it to the team. Be blunt about what's missing." |
| Nothing written down | "I want to blueprint how a new client is onboarded, from contract signed to first use. I have no documents. Where do we start?" |

In the last case Claude asks you questions, one phase at a time, instead of inventing answers.

Blueprints come out in English or European Portuguese. Ask in the language you want, or say which one.

## 4. What you get

- You get a page with the blueprint, which you can open in Claude and share by link.
- You get two data files:
  - `name-frame.yaml` holds the header, phases, lanes, sources and status models.
  - `name-cards.csv` holds one card per row. It opens in Excel or Google Sheets.
- You get the list of what needs a decision, and the results of the quality checks.
- The page footer carries a small credit to the template. The blueprint itself is yours. Ask Claude to remove the credit if you need to.

To change something, ask in plain words: "add a lane for the delivery partner" or "phase 3 has too much detail". Claude changes the data and rebuilds the page.

## 5. How to read the blueprint

**Lanes and lines.** From top to bottom: what the customer receives, what the customer does, the line of interaction, what the customer sees (systems, AI assistant, people), the line of visibility, backstage work, the line of internal interaction, and support processes. Policies and rules (laws, contracts, guardrails for AI agents) sit with the support processes. Supporting documents and exceptions sit at the bottom.

**Columns.** Each column starts with one customer action and its one touchpoint: a screen, a message or a person. Read left to right in time. Arrows start at whoever starts the interaction.

**Markers.** A § card is a rule in force at that step, linked to the decision it governs. A ★ card is a key moment: the step that matters most to the customer, or a moment of delight. Orange stickies are pain points, placed in the lane of whoever feels them. Durations and other measures sit on the card they measure.

**Where each card comes from.** Every card has a basis:

| Label | Meaning |
|---|---|
| evidence | Backed by a source (interview, document, data) |
| decided | A recorded decision |
| proposed | Part of the concept, not decided yet |
| assumption | Inferred, still to confirm |
| TBC | An open question |
| gap | The service needs it and nobody has designed it |

**Exceptions.** Each exception has an owner and a risk for the customer. `unassigned` means nobody owns the problem. That is usually the most useful thing to discuss with the team.

**Releases.** Cards without a tag ship in the first release. Cards tagged R2 and R3 come later. Cards marked Later have no release yet. Cards marked To confirm wait for a decision.

**Levels.** L0 is the end-to-end, strategic journey. L1 is one stage of that journey. L2 is the operational journey of a single touchpoint or vertical.

## 6. Tips

- Say up front whether it is as-is or to-be, which level, and where the service starts and ends.
- Pick one scenario and start with the most common path. A blueprint is not a process map. Problem paths that happen often get their own blueprint.
- Review the skeleton before Claude adds exceptions. Changing the structure early is cheap.
- Use the draft to start the stakeholder workshop, not to skip it. The value of a blueprint is the conversation between the teams that run the service.
- Give sources. Without them Claude marks almost everything as an assumption, and it is right to.
- Summaries made with AI count as secondary sources. Claude treats them that way.
- Don't upload confidential client data without permission.
- Review in the HTML page first. Moving a blueprint to FigJam or Miro uses far more of your usage limit.

## Limitations

- The skill is in beta. It has been tested on examples, not yet on real projects.
- The FigJam and Miro instructions exist but have not been tested.
- On the free plan, a large blueprint can use up the usage limit in a single conversation.

## Feedback

Tried it? Reach out to Daniel and tell him what worked and where it broke. A few lines are enough. Write through [danieltsantos.com](https://danieltsantos.com), or open an [issue](https://github.com/danieltsantos/service-blueprint/issues) if you use GitHub.

## What's in this repository

| Folder | Contents |
|---|---|
| `service-blueprint/` | The skill itself: instructions, notation reference, example files and scripts |
| `service-blueprint/evals/` | Test cases used to check the skill |
| `docs/` | The two example pages published at the links above, and the data files of the Portuguese example |
| `service-blueprint.zip` | The packaged skill, ready to upload to Claude |

## Method

The skill was built from practice and checked against the classic guides. It adds what services with AI agents need: lanes for agents and their handoffs to people, and a basis on every card that says where it comes from. The guides it was checked against are:

- Adaptive Path, *A Guide to Service Blueprinting*, 2016. Licence CC BY-NC 3.0.
- Erik Flowers and Megan Erin Miller, *Your Guide to Blueprinting the Practical Way*, Practical by Design, 2022.
- Gerry Scullion, *7 Ways to Power up your Journey Mapping Skills*, 2024.

## Licence

[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) © 2026 Daniel Santos.

You may use, share and adapt the skill with credit. You may not use it for commercial purposes. Blueprints you make with it are yours.
