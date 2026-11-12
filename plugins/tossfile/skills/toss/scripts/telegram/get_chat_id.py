#!/usr/bin/env python3
"""Connect the user's Telegram chat to the bot and save it as TG_CHAT_ID.

Two steps, so Claude can show the link before it starts waiting:

  get_chat_id.py prepare   prints a one-time link (LINK:, GROUP_LINK:, CODE:)
  get_chat_id.py wait      waits for the user to open the link and press Start

Only a message that carries the one-time code is accepted, so a stranger who
writes to the bot at the same moment cannot take the chat. Uses the HTTP Bot API
only; no extra install.
"""
import argparse
import json
import secrets
import sys
import time

from common import (
    ENV_FILE, PENDING_FILE, BotApiError, bot_api, check_token, ensure_config_file, fail,
    load_config, write_env_value,
)

CONNECTED_TEXT = (
    "Connected. Files from your AI agent will arrive in this chat.\n"
    "You can close this chat now."
)


def prepare(cfg):
    try:
        me = check_token(cfg["TG_BOT_TOKEN"])
    except BotApiError as e:
        fail(str(e))
    code = secrets.token_hex(4)
    ensure_config_file()
    PENDING_FILE.write_text(json.dumps({"code": code, "bot": me["username"], "t": time.time()}))
    print(f"BOT: @{me['username']}")
    print(f"LINK: https://t.me/{me['username']}?start={code}")
    print(f"GROUP_LINK: https://t.me/{me['username']}?startgroup={code}")
    print(f"CODE: {code}")
    print("NEXT: show LINK to the user, then run: get_chat_id.py wait")


def _chat_name(chat):
    return chat.get("title") or " ".join(
        x for x in [chat.get("first_name", ""), chat.get("last_name", "")] if x
    ) or str(chat.get("id"))


def wait(cfg, timeout):
    if not PENDING_FILE.exists():
        fail("No link was made yet. Run: get_chat_id.py prepare")
    code = json.loads(PENDING_FILE.read_text())["code"]
    token = cfg["TG_BOT_TOKEN"]
    try:
        # A webhook blocks getUpdates; a fresh bot has none, but a reused one might.
        bot_api(token, "deleteWebhook", {"drop_pending_updates": False})
    except BotApiError as e:
        fail(str(e))
    print(f"Waiting up to {timeout}s for the user to press Start...", flush=True)
    deadline = time.time() + timeout
    offset = None
    while time.time() < deadline:
        poll = max(1, min(25, int(deadline - time.time())))
        params = {"timeout": poll, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset
        try:
            updates = bot_api(token, "getUpdates", params, timeout=poll + 10)
        except BotApiError as e:
            if "Conflict" in str(e):
                fail("Conflict: another program is reading this bot's messages. Stop it and try again.")
            fail(str(e))
        for u in updates:
            offset = u["update_id"] + 1
            msg = u.get("message") or {}
            text = msg.get("text") or ""
            chat = msg.get("chat") or {}
            if code not in text:
                if chat.get("type") == "private":
                    _reply(token, chat["id"], "Please open the link that your AI agent gave you, then press Start.")
                continue
            write_env_value("TG_CHAT_ID", chat["id"])
            _reply(token, chat["id"], CONNECTED_TEXT)
            bot_api(token, "getUpdates", {"offset": offset, "timeout": 0})  # mark as read
            PENDING_FILE.unlink(missing_ok=True)
            print(f"CONNECTED: {_chat_name(chat)} ({chat.get('type')})")
            print(f"Saved TG_CHAT_ID to {ENV_FILE}")
            return
    fail("Timeout: nobody pressed Start. Run 'get_chat_id.py wait' again; the same link still works.")


def _reply(token, chat_id, text):
    try:
        bot_api(token, "sendMessage", {"chat_id": chat_id, "text": text})
    except BotApiError:
        pass


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("step", choices=["prepare", "wait"])
    p.add_argument("--timeout", type=int, default=180)
    args = p.parse_args()
    cfg = load_config(need_chat=False)
    try:
        prepare(cfg) if args.step == "prepare" else wait(cfg, args.timeout)
    except KeyboardInterrupt:
        sys.exit(130)
