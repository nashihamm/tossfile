---
name: toss
description: Tosses a file (APK, AAB, IPA, zip, or any file up to 2 GB) from this machine to the user's phone; currently delivers to their Telegram chat through their own bot. Use when the user says "send the apk", "send it to telegram", "send this file to my phone", "toss this file", "toss the apk", "kirim apk", "kirim ke telegram", "kirim file ke hp", or right after an Android/Capacitor build finishes and the user wants the build on their phone. Also use for setup and changes: "set up tossfile", "connect telegram", "change my bot", "send to a group", "send big files".
---

# Toss a file

Deliver a file from this machine to the user's phone or chat.

Destinations: Telegram is the only one today. Each destination keeps its scripts in its own folder under `scripts/`. If the user asks for a destination that has no folder there (email, WhatsApp, and so on), say it is not supported yet and offer Telegram.

## How to talk during setup

Setup happens in this chat. The user should never need to open a terminal or edit a file.

- Speak the user's language. The messages below are in simple English. Translate them, but keep them as short and plain.
- One step per message. Wait for the user before the next step.
- Short sentences. Name the exact button or word to tap. No jargon: say "bot token", not "credential"; say "your chat", not "peer".
- After each step, say what worked in one line ("Your bot @x_bot is working.").

## Telegram

All scripts live in `scripts/telegram/` next to this file. Run them with `python3` and the full path. Run them on the machine that has the file. If a run fails with `ConnectionError` inside a cloud sandbox, tell the user the sandbox cannot reach Telegram and the skill must run on their own computer.

How it sends:
- Files up to 50 MB: HTTP Bot API. Needs only the bot token. Nothing to install.
- Files over 50 MB (up to 2000 MB): MTProto through Telethon. Also needs `TG_API_ID` and `TG_API_HASH`. Telethon installs itself into a private environment the first time.

## 1. Check setup

Run `python3 scripts/telegram/setup_config.py`. It never prints secrets. Read the `STATUS:` line:

- `need_token` → step 2a.
- `need_chat` → step 2b.
- `ready` → step 3.

Any script that exits with code 2 and `SETUP_NEEDED` also means: go back to step 1.

## 2. First-time setup (about 2 minutes)

Before step 2a, tell the user in one line: "First time, so let's connect your Telegram. It takes about 2 minutes and you only do it once."

### 2a. Bot token

Send the user this (translated):

> 1. In Telegram, open **@BotFather** (the one with a blue check mark).
> 2. Send `/newbot`.
> 3. Type a name for your bot, for example `My Builds`.
> 4. Type a username that ends with `bot`, for example `myname_builds_bot`.
> 5. BotFather sends a long code, like `123456789:AAH...`. That is your bot token.
>
> Paste the token here. It is saved only on this computer, in `~/.config/tossfile/.env`. If you prefer not to paste it, put it in that file yourself after `TG_BOT_TOKEN=`, then tell me "done".

When the user pastes the token, save it through stdin (never as a command argument, never echoed back):

```
printf 'TG_BOT_TOKEN=%s\n' '<token>' | python3 scripts/telegram/save_config.py
```

- `BOT: @name` → say "Your bot @name is working." and go to 2b.
- `TokenFormat` → the paste is not a token. Ask them to copy the whole line from BotFather (it has a colon in the middle).
- `TokenInvalid` → Telegram rejected it. Maybe the token was revoked. Ask them to send `/token` to @BotFather, pick the bot, and paste the new one.

If the user edited the file themselves, run `setup_config.py` again instead.

Do not repeat the token in any message. Do not save it anywhere else.

### 2b. Connect the chat

1. Run `python3 scripts/telegram/get_chat_id.py prepare`. It prints `LINK:` and `GROUP_LINK:`.
2. Send the user this (translated), with the real link:

   > Now open this link on your phone and tap **Start**:
   > <LINK>
   >
   > I am waiting for it. (Want files in a group instead? Use this link and pick the group: <GROUP_LINK>)

3. In the same turn, right after that message, run `python3 scripts/telegram/get_chat_id.py wait`. It waits up to 180 seconds; give the command at least 200 seconds.
4. Results:
   - `CONNECTED: <name>` → say: "Done. Your bot sent 'Connected' in Telegram. From now on, just say 'send the apk' or 'send <file> to telegram'." Then go on with the user's original request, if any.
   - `Timeout` → ask if they tapped Start. The same link still works; run `wait` again when they say so. Do not run `prepare` again unless the link was lost.
   - `Conflict` → another program reads this bot's messages (often an old webhook or another tool using the same bot). Ask the user to stop it, or to make a new bot for Tossfile.

### 2c. Big files (only when needed)

Do not ask for this during first setup. Ask only when `send_file.py` stops with `BIG_FILE_SETUP_NEEDED` (exit code 3, nothing was sent), or when the user asks for big files.

Send the user this (translated), with the real file size:

> This file is <size>. Telegram bots can send up to 50 MB with the bot token alone. For bigger files (up to 2000 MB), I need two more values. You get them once:
>
> 1. Go to https://my.telegram.org and log in with your phone number. Telegram sends the login code to your Telegram app, not by SMS.
> 2. Tap **API development tools**.
> 3. Fill in the form. App title and short name can be anything, like `tossfile`. Platform: Desktop. URL can stay empty.
> 4. Tap **Create application**.
> 5. Copy **App api_id** (only numbers) and **App api_hash** (32 letters and numbers).
>
> Paste both here, or put them in `~/.config/tossfile/.env` after `TG_API_ID=` and `TG_API_HASH=`.

Then save them the same way as the token:

```
printf 'TG_API_ID=%s\nTG_API_HASH=%s\n' '<id>' '<hash>' | python3 scripts/telegram/save_config.py
```

If the form on my.telegram.org shows only "ERROR", tell the user this is common: try again later, from another browser, or with a VPN off. They can keep sending files under 50 MB meanwhile.

### Changes later

- "Change my bot" or a new token → step 2a again. If the output has `NOTE: new bot`, do 2b after it. If it says `same bot with a new token`, nothing else is needed.
- "Send to a group" / "send to another chat" → step 2b, and give the GROUP_LINK.
- "Send just this once to X" → `send_file.py --chat <id or @username>`; this does not change the saved chat.
- "Remove my setup" → tell the user to delete the folder `~/.config/tossfile`. Do not delete it yourself unless they ask.

## 3. Find the file

If the user named a file or path, use it. Otherwise find the newest build output in the current project:

- Flutter APK: `build/app/outputs/flutter-apk/*.apk`
- Capacitor / native Android APK: `android/app/build/outputs/apk/**/*.apk`
- Android bundle: `android/app/build/outputs/bundle/**/*.aab` or `build/app/outputs/bundle/**/*.aab`
- If nothing is found there, search the project for `*.apk` (skip `node_modules`) and take the most recently modified.

If several candidates were modified in the same build (for example debug and release), pick the one that matches what was just built; ask only when it is truly unclear. Do not rebuild unless asked.

## 4. Send

```
python3 scripts/telegram/send_file.py "<path>" --caption "<caption>"
```

- Several files can be passed in one call; the caption goes on the first.
- Write a short caption when the facts are easy to get: app name, version (`pubspec.yaml` `version`, `android/app/build.gradle` `versionName`, or `package.json`), build type (debug/release), git branch and short commit. Skip any part that is not readily available.
- Big files take time (a 100 MB file can take a few minutes). Give the command a timeout of at least 10 minutes. Progress prints every 10%.

## 5. Report

On `SENT:` lines, tell the user in one short sentence which file was sent and its size. On an error, say the reason in plain words and the fix:

| Output | Meaning and fix |
| :-- | :-- |
| `SETUP_NEEDED` | Setup is not finished. Go to step 1. |
| `BIG_FILE_SETUP_NEEDED` | File is over 50 MB. Go to step 2c. Nothing was sent. |
| `TokenInvalid`, `AccessTokenInvalidError` | The bot token no longer works. Step 2a with a new token from @BotFather (`/token`). |
| `ApiIdInvalidError` | api_id or api_hash is wrong. Step 2c again; copy both again from my.telegram.org. |
| `ChatNotReachable`, `Could not find the input entity`, `PeerIdInvalidError`, `UserIsBlockedError` | The bot cannot write to the chat (blocked, left the group, or chat deleted). Step 2b. |
| `FloodWait` | Telegram asks to wait. Say how many seconds, then retry. |
| `ConnectionError` | This machine cannot reach Telegram (no internet, firewall, cloud sandbox). |
| `Install Certificates.command` in the message | Python on this Mac cannot check HTTPS. Tell the user to open the Python folder in Applications and double-click `Install Certificates.command`. |
