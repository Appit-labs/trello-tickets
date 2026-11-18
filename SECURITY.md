# Security review — trello-tickets

Static analysis with SkillSpector v2.12.0 (no LLM).

- Raw scan: **70/100**, HIGH, DO_NOT_INSTALL, 3 finding(s).
- With the accepted-findings baseline: **0/100, SAFE, 0 open findings**.

Accepted findings live in `.skillspector-baseline.yaml`, so a scan still fails on anything new:

```bash
pip install skillspector
skillspector scan skills/trello-tickets --baseline .skillspector-baseline.yaml
```

## Accepted findings

| Rule | Severity | File | Why acceptable |
| --- | --- | --- | --- |
| TT3 | CRITICAL | `trello.py:121` | Single hard-coded HTTPS endpoint with certificate verification; no user-controlled URL, no redirect to other hosts. |
| E1 | MEDIUM | `trello.py:39` | A documented API endpoint in the instructions, not a runtime choice by the model. |
| TR1 | LOW | `SKILL.md:1` | Several routing phrases in the description are intentional; the skill cannot invoke itself. |

## What this skill never does

- No `shell=True`, no `eval`, no `exec` of model-supplied strings.
- No credentials in the repo, none echoed.
- No runtime choice of network destination.
- No write outside the path the user named.

## Test evidence

Every command in the SKILL.md was run against a real target. `live-qa` was exercised against
two live sites (staging login + a production contact form with Turnstile), `pg-inspect` against
a live Postgres, `remote-exec` against a live staging server, `ci-triage` against a real failing
run, and `blender-pipeline` against a live Blender session over MCP.
