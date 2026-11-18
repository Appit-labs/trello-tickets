# trello-tickets

<h3 align="center">Seven ticket types baked in — no template card to read before filing one.</h3>

<p align="center">
  <a href="LICENSE"><img alt="license" src="https://img.shields.io/badge/license-MIT-3DA639?style=flat-square"></a>
  <img alt="agents" src="https://img.shields.io/badge/works%20in-pi%20%7C%20Claude%20Code%20%7C%20Codex%20%7C%20Cursor-4B5563?style=flat-square">
  <img alt="skillspector" src="https://img.shields.io/badge/SkillSpector-0%2F100%20SAFE-2EA043?style=flat-square">
  <img alt="tokens" src="https://img.shields.io/badge/session%20cost-~96%20tok-6E7681?style=flat-square">
</p>

<p align="center">
  <img alt="trello-tickets demo" src="skills/trello-tickets/assets/demo.gif" width="820">
</p>

## Install

One command for each agent — the skill is plain Markdown plus a script, so nothing is coupled to one ecosystem.

```bash
# Claude Code (plugin, stays updatable)
claude plugin marketplace add Appit-labs/appit-skills
claude plugin install trello-tickets@appit-skills

# pi
pi install git:github.com/Appit-labs/trello-tickets

# any agent that reads a skills directory
git clone git@github.com:Appit-labs/trello-tickets.git
cp -r trello-tickets/skills/trello-tickets ~/.claude/skills/      # or ~/.codex/skills/, .cursor/skills/, …
```

## Why this exists

Ticket templates live in someone's head or in a card you must read first. Here they are data: sections, checklist, labels and cover colour come with the type, so a well-formed card is one command.

## Use

- Read: `boards` · `lists "Board"` · `cards "Board" --list "Next Sprint"` · `card <id>`
- Inspect a type: `scripts/trello.py template "Defect Template"` — works offline`
- Create: `scripts/trello.py create "Board" --list "Next Sprint" --type "Task Template" --title … --dry-run`

## Requires

- Python 3.9+ (stdlib only).
- A Trello API key and token: `scripts/trello.py login --key … --token …` (writes `~/.config/trello/config.json`, mode 600). Env vars override.
- Network access to `api.trello.com` (or your own `TRELLO_API_BASE`).

## What you get

- `--dry-run` prints the exact payload; creating a card notifies the board and cannot be un-notified.
- Types: User Story · Task · Documentation (rst) · Defect · Technical Debt · Spike · Distraction.
- No credentials in the repo; the merged helper is visible to agents instead of being a hidden script.

## Cost

| | tokens |
| --- | --- |
| always-on (the description, every session) | ~96 |
| on invoke | ~1k |

The demo above is regenerated from a real run: `demos/trello-tickets.json` holds the captured
output, `tools/make_demo.py` renders it. No invented screenshots.

## Security

Static analysis with SkillSpector: **0/100, SAFE, 0 open findings** against the committed
baseline. Every accepted finding is listed with its reason in [SECURITY.md](SECURITY.md).
The skill never uses `shell=True`, never reads or stores a credential, and never chooses a
network destination at runtime.

## Part of the Appit collection

Browser QA · CI triage · Postgres · runbooks · SSH · Trello · cloud browsers · OpenDesign · Blender —
one marketplace: [appit-skills](https://github.com/Appit-labs/appit-skills).

## License

MIT. See [LICENSE](LICENSE).
