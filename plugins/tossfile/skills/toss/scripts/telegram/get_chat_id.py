#!/usr/bin/env python3
"""Wait for the next message sent to the bot and save that chat as TG_CHAT_ID.
Start this script first, THEN send any message to the bot in Telegram."""
import argparse
import asyncio

from common import ensure_telethon, fail, load_config, make_client, start_bot, write_env_value, ENV_FILE

ensure_telethon()
from telethon import events  # noqa: E402


async def main(timeout):
    cfg = load_config(need_chat=False)
    client = make_client(cfg)
    await start_bot(client, cfg)
    me = await client.get_me()
    print(f"Bot @{me.username} is listening. Send it any message now "
          f"(waiting up to {timeout}s)...", flush=True)
    found = asyncio.get_running_loop().create_future()

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if not found.done():
            found.set_result(event)

    try:
        event = await asyncio.wait_for(found, timeout)
    except asyncio.TimeoutError:
        await client.disconnect()
        fail("No message arrived. Open the bot in Telegram, press Start, send 'hi', and run again.")
    chat = await event.get_chat()
    name = getattr(chat, "title", None) or " ".join(
        x for x in [getattr(chat, "first_name", ""), getattr(chat, "last_name", "")] if x
    )
    write_env_value("TG_CHAT_ID", event.chat_id)
    await event.reply("Connected. Build files will arrive in this chat.")
    await client.disconnect()
    print(f"Saved chat {event.chat_id} ({name}) to {ENV_FILE}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--timeout", type=int, default=120)
    asyncio.run(main(p.parse_args().timeout))
