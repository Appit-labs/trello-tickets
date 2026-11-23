---
name: trello-tickets
description: Read and create Trello cards from a fixed set of ticket types (User Story, Task, Documentation, Defect, Technical Debt, Spike, Distraction) with the right description sections, checklist, labels, and cover color — and read boards, lists, and cards back. Use when the user asks to file, create, add, or open a Trello ticket/card, or to list, read, or inspect what is on a Trello board.
allowed-tools:
  - Bash
  - Read
permissions:
  - network
  - env
  - file_write
license: MIT
---

# Trello tickets

One helper, two jobs: create a card from a ticket type, or read a board.

```
python3 "$SKILL_DIR/scripts/trello.py" <command>
```

`templates` and `template <type>` work offline (no credentials). Everything that
touches a board needs an API key and token.

**Not for:** board administration (creating boards and lists, Butler rules, members) — this creates and reads cards. Jira, Linear or GitHub Issues need their own skill.

## Portability

Works in any agent that can run shell commands (pi, Claude Code, Codex, Cursor,
Gemini CLI, …): the instructions are plain Markdown and the helper is a stdlib
script. Commands use `$SKILL_DIR` for this skill's own directory — the folder that
holds this `SKILL.md`. Set it once per session, for example:

```bash
SKILL_DIR=~/.claude/skills/trello-tickets     # or ~/.codex/skills/…, ~/.pi/agent/skills/…, .cursor/skills/…
```

## Prerequisites

1. A Trello API key: <https://trello.com/power-ups/admin> → your Power-Up → **API key**.
2. A token: click **Token** on that same page.
3. Store them once:

```bash
python3 "$SKILL_DIR/scripts/trello.py" login --key KEY --token TOKEN
```

Writes `~/.config/trello/config.json` with mode 600, verifies the pair against the
API, and prints the account it belongs to. Env vars `TRELLO_API_KEY` and
`TRELLO_TOKEN` override the file (useful in CI). Nothing is ever printed back.

Needs network access to `api.trello.com` only; the script is stdlib Python.

## Reading

```bash
... boards                          # every board you can see: Name<TAB>id
... lists  "My Board"                # lists on a board
... cards  "My Board" --list "Next Sprint"
... card   <card_id>                # full card: description, checklists, labels, comments
```

Boards, lists and labels resolve by **name or id**, case-insensitively, so the user
can say "my board" and it works. When two boards share a name the script
errors and lists the candidates instead of guessing.

## Ticket types

| Type | Use for | Cover |
| --- | --- | --- |
| User Story | a feature or capability | green |
| Task | a concrete dev task | blue |
| Documentation (rst file) | docstrings, module docs | sky |
| Defect | a bug or broken behaviour | red |
| Technical Debt | refactor / cleanup, nothing user-facing | black |
| Spike | investigation or research | yellow |
| Distraction | unplanned context switch | purple |

Each type carries its default description sections, checklist, and labels —
baked in, so creating a card needs no board read. Inspect one with
`template "Defect Template"`; list all with `templates`.

## Creating

```bash
... create "My Board" --list "Next Sprint" --type "Task Template" \
      --title "Add retry to the PDF exporter" \
      --desc "..." --attach ./screenshot.png --cover
```

- `--checkitem "..."` (repeatable) adds checklist items beyond the defaults.
- `--labels "backend,bug"` resolves label names on that board; unknown labels are
  reported, not silently dropped.
- `--dry-run` prints the exact payload and creates nothing.
- **Always `--dry-run` first when the user has not seen the card text**, then run
  for real. Creating a card notifies the whole board — there is no undo that
  removes the notification.
- Screenshots: pass `--attach`, and `--cover` only when the image is meaningful as
  a thumbnail (a UI screenshot usually is, a log dump is not).

## Fill the template, do not invent structure

Keep the section headings the type defines; replace placeholder text with real
content. A Defect card without reproduction steps, or a Spike without a
time-box and a question to answer, is the failure mode this skill exists to
prevent. If the user's request does not fit any type, say which two are closest
and pick one — do not invent an eighth type.

## Reporting

After creating, return the short link and the list it landed in. After reading,
summarise; do not dump raw JSON unless the user asked for data.
