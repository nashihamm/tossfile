---
name: toss
description: Tosses a file (APK, AAB, IPA, zip, or any file up to 2 GB) from this machine to the user's phone; currently delivers to their Telegram chat through their own bot. Use when the user says "send the apk", "send it to telegram", "send this file to my phone", "toss this file", "toss the apk", "kirim apk", "kirim ke telegram", "kirim file ke hp", or right after an Android/Capacitor build finishes and the user wants the build on their phone. Also handles first-time setup of the bot.
---

# Toss a file

Deliver a file from this machine to the user's phone or chat.

Destinations: Telegram is the only one today. Each destination keeps its scripts in its own folder under `scripts/`. If the user asks for a destination that has no folder there (email, WhatsApp, and so on), say it is not supported yet and offer Telegram.

## Telegram

Deliver a file to the user's Telegram chat with the bundled scripts. The scripts log in as the user's bot over MTProto (Telethon), so files up to 2000 MB work; the 50 MB HTTP Bot API limit does not apply.

All scripts live in `scripts/telegram/` next to this file. Run them with `python3`, passing the full path. They install Telethon into a private environment on first run; no manual `pip install` is needed.

Run the scripts on the machine that has the file and normal internet access. If this session has a shell on the user's computer, run them there. If a run ends with a connection error inside a cloud sandbox, tell the user the sandbox cannot reach Telegram and the skill must run on their own computer.

## 1. Check setup

Run `python3 scripts/telegram/setup_config.py`. It creates the private config file if missing and prints which values are set. It never prints secrets.

- `STATUS: ready` → go to step 3.
- `STATUS: run get_chat_id.py next` → go to step 2b.
- Otherwise → go to step 2a.

Also treat exit code 2 with `SETUP_NEEDED` from any script as "setup is incomplete".

## 2. First-time setup

### 2a. Keys

Tell the user the config file path that `setup_config.py` printed and ask them to open it and fill in three values themselves:

- `TG_BOT_TOKEN`: create a bot with @BotFather in Telegram (`/newbot`) and copy the token.
- `TG_API_ID` and `TG_API_HASH`: sign in at https://my.telegram.org, open "API development tools", create an app (any name), copy both values.

Prefer that the user edits the file directly instead of pasting secrets into the chat. If they paste the values in chat anyway, write them into the config file for them. Never print, echo, log, or commit these values, and never copy the config file into a project folder.

When the user says the values are in, run `setup_config.py` again to confirm.

### 2b. Chat ID

1. Tell the user first: "Open your bot in Telegram, press Start, and send it any message in the next two minutes."
2. Then run `python3 scripts/telegram/get_chat_id.py` (it waits up to 120 seconds; allow that much time for the command).
3. On success it saves the chat and the bot replies "Connected" in Telegram. To deliver into a group instead, the user adds the bot to the group and sends a message there while the script is waiting.

## 3. Find the file

If the user named a file or path, use it. Otherwise find the newest build output in the current project:

- Capacitor / native Android APK: `android/app/build/outputs/apk/**/*.apk`
- Android bundle: `android/app/build/outputs/bundle/**/*.aab`
- If nothing is found there, search the project for `*.apk` (skip `node_modules`) and take the most recently modified.

If several candidates were modified in the same build (for example debug and release), pick the one that matches what was just built; ask only when it is truly unclear. Do not rebuild unless asked.

## 4. Send

```
python3 scripts/telegram/send_file.py "<path>" --caption "<caption>"
```

- Several files can be passed in one call; the caption goes on the first.
- Write a short caption when the facts are easy to get: app name, version (from `android/app/build.gradle` `versionName` or `package.json`), build type (debug/release), git branch and short commit. Skip any part that is not readily available.
- Large files take time (a 100 MB file can take a few minutes). Give the command a timeout of at least 10 minutes. Progress prints every 10%.
- `--chat <id or @username>` sends to a different chat once, without changing the saved one.

## 5. Report

On `SENT:` lines, tell the user in one short sentence which file was sent and its size. On an error, report the reason shown and the fix:

- `SETUP_NEEDED` → go to step 2.
- `AccessTokenInvalidError` / `ApiIdInvalidError` → the bot token or api_id/api_hash is wrong; ask the user to correct the config file.
- `Could not find the input entity` / `PeerIdInvalidError` / `UserIsBlockedError` → the user has not started the bot or blocked it; redo step 2b.
- `FloodWaitError` → Telegram asks to wait; say how many seconds and retry after that.
- `ConnectionError` → no route to Telegram from this machine (see the note at the top).
