#!/usr/bin/env python3
"""Send one or more files to the configured Telegram chat through the bot.

Files up to 50 MB go over the HTTP Bot API (no extra install). Bigger files, up
to 2000 MB, go over MTProto (Telethon) and need TG_API_ID and TG_API_HASH; if
those are missing the script stops before sending anything with BIG_FILE_SETUP_NEEDED.
"""
import argparse
import asyncio
import http.client
import json
import mimetypes
import os
import secrets
import ssl
import sys
import time

from common import (
    ENV_FILE, HTTP_LIMIT, MTPROTO_LIMIT, fail, has_big_file_keys, load_config, parse_chat,
)


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


# --- HTTP Bot API, files up to 50 MB ------------------------------------------

def send_http(cfg, chat, path, caption):
    name = os.path.basename(path)
    boundary = "tossfile" + secrets.token_hex(12)
    fields = {"chat_id": str(chat)}
    if caption:
        fields["caption"] = caption
    head = b""
    for k, v in fields.items():
        head += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n").encode()
    ctype = mimetypes.guess_type(name)[0] or "application/octet-stream"
    safe_name = name.replace('"', "_")
    head += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"document\"; "
             f"filename=\"{safe_name}\"\r\nContent-Type: {ctype}\r\n\r\n").encode()
    tail = f"\r\n--{boundary}--\r\n".encode()
    size = os.path.getsize(path)

    conn = http.client.HTTPSConnection("api.telegram.org", timeout=120)
    try:
        conn.putrequest("POST", f"/bot{cfg['TG_BOT_TOKEN']}/sendDocument")
        conn.putheader("Content-Type", f"multipart/form-data; boundary={boundary}")
        conn.putheader("Content-Length", str(len(head) + size + len(tail)))
        conn.endheaders()
        conn.send(head)
        report = progress_printer(name)
        sent = 0
        with open(path, "rb") as f:
            while chunk := f.read(256 * 1024):
                conn.send(chunk)
                sent += len(chunk)
                report(sent, size)
        conn.send(tail)
        body = json.loads(conn.getresponse().read().decode())
    except (OSError, ssl.SSLError, http.client.HTTPException) as e:
        fail(f"ConnectionError: could not reach Telegram ({e}).")
    finally:
        conn.close()
    if not body.get("ok"):
        code, desc = body.get("error_code"), body.get("description", "")
        if code == 401:
            fail("TokenInvalid: Telegram does not accept the bot token.")
        if code == 403 or "chat not found" in desc:
            fail(f"ChatNotReachable: {desc}. Connect the chat again.")
        if code == 429:
            fail(f"FloodWait: wait {body.get('parameters', {}).get('retry_after', '?')} seconds.")
        fail(f"Telegram refused the file: {desc} (code {code})")
    return body["result"]["message_id"]


# --- MTProto, files up to 2000 MB ---------------------------------------------

async def send_mtproto(cfg, chat, files, caption):
    from common import make_client, start_bot
    client = make_client(cfg)
    await start_bot(client, cfg)
    try:
        for path, cap in zip(files, caption):
            name = os.path.basename(path)
            print(f"Sending {name} ({human(os.path.getsize(path))}) over MTProto...", flush=True)
            msg = await client.send_file(
                chat, path, caption=cap, force_document=True,
                progress_callback=progress_printer(name),
            )
            print(f"SENT: {name} (message id {msg.id})", flush=True)
    finally:
        await client.disconnect()


def main(args):
    for f in args.files:
        if not os.path.isfile(f):
            fail(f"File not found: {f}")
        if os.path.getsize(f) > MTPROTO_LIMIT:
            fail(f"{f} is over 2000 MB, the Telegram limit for bots.")
    cfg = load_config()
    chat = parse_chat(args.chat or cfg["TG_CHAT_ID"])
    big = [f for f in args.files if os.path.getsize(f) > HTTP_LIMIT]
    if big and not has_big_file_keys(cfg):
        names = ", ".join(f"{os.path.basename(f)} ({human(os.path.getsize(f))})" for f in big)
        print(f"BIG_FILE_SETUP_NEEDED: {names} is over 50 MB. Add TG_API_ID and TG_API_HASH "
              f"to {ENV_FILE} to send files up to 2000 MB. Nothing was sent.", file=sys.stderr)
        sys.exit(3)
    if big:
        from common import ensure_telethon
        # May re-run this whole script inside the private venv, so do it before sending anything.
        ensure_telethon()

    captions = [args.caption] + [None] * (len(args.files) - 1)
    small = [(f, c) for f, c in zip(args.files, captions) if f not in big]
    for f, cap in small:
        name = os.path.basename(f)
        print(f"Sending {name} ({human(os.path.getsize(f))})...", flush=True)
        mid = send_http(cfg, chat, f, cap)
        print(f"SENT: {name} (message id {mid})", flush=True)
    if big:
        cfg = load_config(need_api=True)
        big_caps = [c for f, c in zip(args.files, captions) if f in big]
        asyncio.run(send_mtproto(cfg, chat, big, big_caps))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("files", nargs="+", help="path(s) of the file(s) to send")
    p.add_argument("--caption", default=None, help="text shown under the first file")
    p.add_argument("--chat", default=None, help="override the saved chat id")
    try:
        main(p.parse_args())
    except KeyboardInterrupt:
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as e:  # show a short reason instead of a long traceback
        fail(f"{type(e).__name__}: {e}")
