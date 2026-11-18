#!/usr/bin/env python3
"""Trello helper CLI: read tickets, and create tickets from baked-in templates.

Templates are static (see templates.py) — no board read is needed to create a
ticket. Reading tickets still hits the API.

Credentials (first match wins):
  env: TRELLO_API_KEY / TRELLO_TOKEN
  ~/.config/trello/config.json  (written by `trello.py login`)

Usage:
  python3 trello.py boards
  python3 trello.py lists <board>
  python3 trello.py cards <board> [--list NAME]
  python3 trello.py card <card_id>
  python3 trello.py templates
  python3 trello.py template <type>
  python3 trello.py create <board> --list NAME --type "Task Template" \
                  --title "..." [--desc "..." ] [--checklist NAME] \
                  [--checkitem "..." ...] [--labels "a,b"] \
                  [--attach /path/img.png ...] [--cover] [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from templates import TEMPLATES  # noqa: E402

API = os.environ.get("TRELLO_API_BASE", "https://api.trello.com/1").rstrip("/")
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "trello"
CONFIG_FILE = CONFIG_DIR / "config.json"


# ---------------------------------------------------------------- auth

def load_creds() -> tuple[str, str]:
    """env vars first, then ~/.config/trello/config.json (mode 600)."""
    key = os.environ.get("TRELLO_API_KEY", "")
    token = os.environ.get("TRELLO_TOKEN", "")
    if (not key or not token) and CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
        except (OSError, ValueError):
            data = {}
        key = key or str(data.get("api_key", ""))
        token = token or str(data.get("token", ""))
    return key, token


def save_creds(key: str, token: str) -> Path:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({"api_key": key, "token": token}, indent=2) + "\n")
    CONFIG_FILE.chmod(0o600)
    return CONFIG_FILE


def cmd_login(args) -> None:
    key = args.key or os.environ.get("TRELLO_API_KEY", "")
    token = args.token or os.environ.get("TRELLO_TOKEN", "")
    if not key or not token:
        print("Get both values here, then re-run with --key and --token:\n"
              "  https://trello.com/power-ups/admin  ->  your Power-Up  ->  API key\n"
              "  then click 'Token' on that page to mint a token for your account.\n\n"
              "  trello.py login --key KEY --token TOKEN", file=sys.stderr)
        raise SystemExit(2)
    path = save_creds(key, token)
    me = api("GET", "/members/me", {"key": key, "token": token, "fields": "username"})
    print(f"saved {path} (600) for @{me.get('username', '?')}")


def creds() -> dict:
    key, token = load_creds()
    if not key or not token:
        print("Missing Trello credentials. Run `trello.py login --key ... --token ...`, or export "
              "TRELLO_API_KEY / TRELLO_TOKEN.", file=sys.stderr)
        raise SystemExit(2)
    return {"key": key, "token": token}


# ---------------------------------------------------------------- http

def _multipart(fields: dict, file_name: str, content: bytes) -> tuple[bytes, str]:
    boundary = "----trello" + os.urandom(8).hex()
    parts: list[bytes] = []
    for k, v in fields.items():
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode())
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{file_name}\"\r\n"
        f"Content-Type: application/octet-stream\r\n\r\n".encode()
        + content + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def api(method: str, path: str, params: dict, body: dict | None = None,
        attachment: tuple[str, bytes] | None = None):
    q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{API}{path}" + (f"?{q}" if q else "")
    data = None
    headers: dict[str, str] = {}
    if attachment:
        name, content = attachment
        data, ctype = _multipart(body or {}, name, content)
        headers["Content-Type"] = ctype
    elif body:
        data = urllib.parse.urlencode(body).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode()
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        raise SystemExit(f"Trello API error {e.code} on {method} {path}: {detail[:400]}")
    except urllib.error.URLError as e:
        raise SystemExit(f"cannot reach {API} ({e.reason}); check network, TRELLO_API_BASE, or the key/token")


# ---------------------------------------------------------------- resolution

def resolve_board(c: dict, name_or_id: str) -> dict:
    if len(name_or_id) in (24, 32) and "-" not in name_or_id:
        return {"id": name_or_id, "name": name_or_id}
    boards = api("GET", "/members/me/boards", {**c, "filter": "open", "fields": "name"})
    for b in boards:
        if b["name"].lower() == name_or_id.lower():
            return b
    raise SystemExit(f"board '{name_or_id}' not found. Available: "
                     + ", ".join(b["name"] for b in boards))


def resolve_list(c: dict, board_id: str, name_or_id: str) -> dict:
    lists = api("GET", f"/boards/{board_id}/lists", {**c, "filter": "open"})
    for lst in lists:
        if lst["id"] == name_or_id or lst["name"].lower() == name_or_id.lower():
            return lst
    raise SystemExit(f"list '{name_or_id}' not found on board {board_id}. Available: "
                     + ", ".join(l["name"] for l in lists))


def resolve_labels(c: dict, board_id: str, names: list[str]) -> list[str]:
    existing = api("GET", f"/boards/{board_id}/labels", {**c, "limit": 1000})
    by_name = {l.get("name", "").lower(): l["id"] for l in existing if l.get("name")}
    ids: list[str] = []
    for n in names:
        lid = by_name.get(n.lower())
        if lid:
            ids.append(lid)
        else:
            l = api("POST", "/labels", c, {"name": n, "color": "blue", "idBoard": board_id})
            ids.append(l["id"])
    return ids


def resolve_type(name: str) -> dict:
    for key, tpl in TEMPLATES.items():
        if key.lower() == name.lower():
            return tpl
    raise SystemExit(f"type '{name}' not found. Available: " + ", ".join(TEMPLATES))


def resolve_me(c: dict) -> dict:
    return api("GET", "/members/me", {**c, "fields": "id,fullName,username"})


# ---------------------------------------------------------------- commands

def cmd_boards(c: dict) -> None:
    for b in api("GET", "/members/me/boards", {**c, "filter": "open", "fields": "name"}):
        print(f"{b['name']}\t{b['id']}")


def cmd_lists(c: dict, board: str) -> None:
    b = resolve_board(c, board)
    for l in api("GET", f"/boards/{b['id']}/lists", {**c, "filter": "open"}):
        print(f"{l['name']}\t{l['id']}")


def _card_fields() -> str:
    return "name,desc,idList,labels,due,shortUrl,isTemplate,idAttachmentCover,idMembers"


def cmd_cards(c: dict, board: str, list_name: str | None) -> None:
    b = resolve_board(c, board)
    if list_name:
        lst = resolve_list(c, b["id"], list_name)
        cards = api("GET", f"/lists/{lst['id']}/cards", {**c, "filter": "open", "fields": _card_fields()})
    else:
        cards = api("GET", f"/boards/{b['id']}/cards", {**c, "filter": "open", "fields": _card_fields()})
    for card in cards:
        labels = ",".join(l.get("name", "") for l in card.get("labels", []))
        tpl = " [TEMPLATE]" if card.get("isTemplate") else ""
        short = card.get("shortUrl", "")
        print(f"{card['name']}\t{card['id']}\t{short}\tlabels={labels}{tpl}")


def cmd_card(c: dict, card_id: str) -> None:
    card = api("GET", f"/cards/{card_id}", {**c, "fields": "name,desc,shortUrl,due,url"})
    checklists = api("GET", f"/cards/{card_id}/checklists", {**c})
    if not isinstance(checklists, list):
        checklists = []
    attachments = api("GET", f"/cards/{card_id}/attachments", {**c, "fields": "name,url,isUpload"})
    print(f"# {card.get('name')}")
    print(f"url: {card.get('url')}")
    if card.get("due"):
        print(f"due: {card.get('due')}")
    print("\n## Description\n" + (card.get("desc") or "(empty)"))
    for cl in checklists:
        print(f"\n## Checklist: {cl.get('name')}")
        for item in cl.get("checkItems", []):
            print(f"- [{'x' if item.get('state') == 'complete' else ' '}] {item.get('name')}")
    if attachments:
        print("\n## Attachments")
        for a in attachments:
            print(f"- {a.get('name')}: {a.get('url')}")


def cmd_templates() -> None:
    for name in TEMPLATES:
        print(name)


def cmd_template(name: str) -> None:
    tpl = resolve_type(name)
    print(tpl["desc"])
    print(f"\n## Checklist: {tpl['checklist']}")
    for item in tpl["checkitems"]:
        print(f"- [ ] {item}")


def cmd_create(c: dict, board: str, list_name: str, typ: str, title: str | None,
               desc: str | None, checklist: str | None, checkitems: list[str],
               labels: str | None, attaches: list[str], cover: bool, dry_run: bool) -> None:
    tpl = resolve_type(typ)
    b = resolve_board(c, board)
    lst = resolve_list(c, b["id"], list_name)
    me = resolve_me(c)

    new_name = title or typ
    final_desc = desc if desc is not None else tpl["desc"]
    final_checklist = checklist or tpl["checklist"]
    final_items = checkitems if checkitems else tpl["checkitems"]
    extra = [x.strip() for x in (labels or "").split(",") if x.strip()]
    label_names = list(dict.fromkeys(list(tpl["labels"]) + extra))

    if dry_run:
        print(f"[DRY RUN] create card '{new_name}' (type {typ}) on list '{lst['name']}' (board {b['name']})")
        print(f"  desc: {len(final_desc)} chars; checklist '{final_checklist}' with {len(final_items)} item(s)")
        if label_names:
            print(f"  labels: {label_names}")
        print(f"  assignee: {me.get('fullName') or me.get('username')} (default = you)")
        if tpl.get("cover"):
            print(f"  cover color: {tpl['cover']['color']}"
                  + (" (replaced by image cover)" if cover and attaches else ""))
        for a in attaches:
            print(f"  would attach: {a}" + (" (cover)" if cover and a == attaches[0] else ""))
        return

    body = {"idList": lst["id"], "name": new_name, "desc": final_desc, "idMembers": me.get("id", "")}
    if label_names:
        body["idLabels"] = ",".join(resolve_labels(c, b["id"], label_names))
    card = api("POST", "/cards", c, body)
    print(f"Created: {card.get('name')}  {card.get('shortUrl')}")
    print(f"  assigned to: {me.get('fullName') or me.get('username')}")

    if final_items:
        cl = api("POST", "/checklists", c, {"idCard": card["id"], "name": final_checklist})
        for item in final_items:
            api("POST", f"/checklists/{cl['id']}/checkItems", c, {"name": item})
        print(f"  checklist '{final_checklist}' ({len(final_items)} items)")

    image_cover = False
    for i, path in enumerate(attaches):
        p = Path(path)
        if not p.exists():
            print(f"  ! attachment not found: {path}")
            continue
        att = api("POST", f"/cards/{card['id']}/attachments", c, None,
                  attachment=(p.name, p.read_bytes()))
        print(f"  attached: {p.name}")
        if cover and i == 0:
            api("POST", f"/cards/{card['id']}/idAttachmentCover", c, {"value": att.get("id")})
            print("  set as cover")
            image_cover = True

    if not image_cover and tpl.get("cover"):
        cv = tpl["cover"]
        api("PUT", f"/cards/{card['id']}", c, {
            "cover[color]": cv["color"],
            "cover[brightness]": cv.get("brightness", "light"),
            "cover[size]": cv.get("size", "normal"),
        })
        print(f"  cover color: {cv['color']}")


# ---------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description="Trello read/create helper.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("boards")
    p_lists = sub.add_parser("lists"); p_lists.add_argument("board")
    p_cards = sub.add_parser("cards"); p_cards.add_argument("board"); p_cards.add_argument("--list")
    p_card = sub.add_parser("card"); p_card.add_argument("card_id")
    sub.add_parser("templates")
    p_tpl = sub.add_parser("template"); p_tpl.add_argument("type")
    p_login = sub.add_parser("login"); p_login.add_argument("--key"); p_login.add_argument("--token")

    p_create = sub.add_parser("create")
    p_create.add_argument("board")
    p_create.add_argument("--list", required=True)
    p_create.add_argument("--type", required=True)
    p_create.add_argument("--title")
    p_create.add_argument("--desc")
    p_create.add_argument("--checklist")
    p_create.add_argument("--checkitem", action="append", default=[])
    p_create.add_argument("--labels")
    p_create.add_argument("--attach", action="append", default=[])
    p_create.add_argument("--cover", action="store_true")
    p_create.add_argument("--dry-run", action="store_true")

    args = ap.parse_args()

    if args.cmd == "login":
        cmd_login(args)
        return 0
    if args.cmd == "templates":
        cmd_templates()
        return 0
    if args.cmd == "template":
        cmd_template(args.type)
        return 0

    c = creds()

    if args.cmd == "boards":
        cmd_boards(c)
    elif args.cmd == "lists":
        cmd_lists(c, args.board)
    elif args.cmd == "cards":
        cmd_cards(c, args.board, args.list)
    elif args.cmd == "card":
        cmd_card(c, args.card_id)
    elif args.cmd == "create":
        cmd_create(c, args.board, args.list, args.type, args.title, args.desc,
                   args.checklist, args.checkitem, args.labels, args.attach,
                   args.cover, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
