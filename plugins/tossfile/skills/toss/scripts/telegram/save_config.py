#!/usr/bin/env python3
"""Check and save setup values that the user gave in the chat.

Reads KEY=VALUE lines from stdin, so the values never sit in the command line:

  printf 'TG_BOT_TOKEN=%s\\n' '<token>' | python3 save_config.py

Allowed keys: TG_BOT_TOKEN, TG_API_ID, TG_API_HASH. Each value is checked before
it is saved (the token with Telegram itself). Never prints the values.
"""
import sys
from pathlib import Path

from common import (
    API_HASH_RE, ENV_FILE, SESSION, BotApiError, check_token, ensure_config_file, fail,
    read_env, write_env_value,
)

ALLOWED = ["TG_BOT_TOKEN", "TG_API_ID", "TG_API_HASH"]


def main():
    pairs = {}
    for line in sys.stdin.read().splitlines():
        line = line.strip()
        if not line or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip().upper(), v.strip().strip('"').strip("'")
        if k not in ALLOWED:
            fail(f"Unknown key {k}. Allowed: {', '.join(ALLOWED)}.")
        if not v:
            fail(f"{k} is empty.")
        pairs[k] = v
    if not pairs:
        fail("Nothing to save. Pipe KEY=VALUE lines into this script.")

    if "TG_BOT_TOKEN" in pairs:
        try:
            me = check_token(pairs["TG_BOT_TOKEN"])
        except BotApiError as e:
            fail(str(e))
        print(f"BOT: @{me['username']} ({me.get('first_name', '')})")
        print(f"LINK: https://t.me/{me['username']}")
    if "TG_API_ID" in pairs and not pairs["TG_API_ID"].isdigit():
        fail("ApiIdFormat: TG_API_ID is only numbers, like 1234567.")
    if "TG_API_HASH" in pairs and not API_HASH_RE.match(pairs["TG_API_HASH"].lower()):
        fail("ApiHashFormat: TG_API_HASH is 32 letters and numbers (0-9, a-f).")
    if "TG_API_HASH" in pairs:
        pairs["TG_API_HASH"] = pairs["TG_API_HASH"].lower()

    ensure_config_file()
    old = read_env()
    old_token, new_token = old.get("TG_BOT_TOKEN") or "", pairs.get("TG_BOT_TOKEN")
    if new_token and old_token and old_token != new_token:
        # The Telethon login was made with the old token; drop it either way.
        for f in (Path(SESSION + ".session"), Path(SESSION + ".session-journal")):
            f.unlink(missing_ok=True)
        if old_token.split(":")[0] != new_token.split(":")[0]:
            # A different bot: the saved chat belongs to the old bot.
            write_env_value("TG_CHAT_ID", "")
            print("NOTE: new bot, so the saved chat was cleared. Connect the chat again.")
        else:
            print("NOTE: same bot with a new token; the saved chat still works.")
    for k, v in pairs.items():
        write_env_value(k, v)
        print(f"SAVED: {k}")
    print(f"Config file: {ENV_FILE}")


if __name__ == "__main__":
    main()
