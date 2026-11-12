#!/usr/bin/env python3
"""Send one or more files to the configured Telegram chat through the bot.
Uses MTProto (Telethon), so it is not bound by the 50 MB HTTP Bot API limit."""
import argparse
import asyncio
import os
import sys
import time

from common import ensure_telethon, fail, load_config, make_client, parse_chat, start_bot

ensure_telethon()

MAX_BYTES = 2000 * 1024 * 1024


def human(n):
    return f"{n / 1024 / 1024:.1f} MB"


def progress_printer(name):
    state = {"next": 10, "t0": time.time()}

    def cb(sent, total):
        pct = sent * 100 // total if total else 100
        if pct >= state["next"]:
            state["next"] = pct - pct % 10 + 10
            rate = sent / max(time.time() - state["t0"], 0.001)
            print(f"  {name}: {pct}% ({human(sent)} of {human(total)}, {human(rate)}/s)", flush=True)
    return cb


async def main(args):
    for f in args.files:
        if not os.path.isfile(f):
            fail(f"File not found: {f}")
        if os.path.getsize(f) > MAX_BYTES:
            fail(f"{f} is over 2000 MB, the Telegram limit for bots.")
    cfg = load_config()
    chat = parse_chat(args.chat or cfg["TG_CHAT_ID"])
    client = make_client(cfg)
    await start_bot(client, cfg)
    try:
        for i, f in enumerate(args.files):
            name = os.path.basename(f)
            print(f"Sending {name} ({human(os.path.getsize(f))})...", flush=True)
            msg = await client.send_file(
                chat, f,
                caption=args.caption if i == 0 else None,
                force_document=True,
                progress_callback=progress_printer(name),
            )
            print(f"SENT: {name} (message id {msg.id})", flush=True)
    finally:
        await client.disconnect()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("files", nargs="+", help="path(s) of the file(s) to send")
    p.add_argument("--caption", default=None, help="text shown under the first file")
    p.add_argument("--chat", default=None, help="override the saved chat id")
    try:
        asyncio.run(main(p.parse_args()))
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:  # show a short reason instead of a long traceback
        fail(f"{type(e).__name__}: {e}")
