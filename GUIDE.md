# Tossfile guide

This guide is for people who use Tossfile. It uses simple English.

You do all of this by talking to Claude. You do not need a terminal. You do not need to edit files.

## What Tossfile does

You build an app on your computer. Tossfile sends the file to your phone through Telegram.

You say "send the apk to telegram". A few seconds later the file is in your Telegram chat. Tap it to install.

It works with any file: APK, AAB, IPA, ZIP, PDF, and others.

## Why you make your own bot

Tossfile has no server and no shared bot. Your files go from your computer to Telegram, then to you. Nobody else sees them.

So you need your own Telegram bot. A bot is free and takes about one minute to make.

## Setup: about 2 minutes, only once

Say to Claude:

> set up tossfile

Claude guides you step by step. It looks like this:

### Step 1: Make a bot

1. In Telegram, open **@BotFather**. It has a blue check mark.
2. Send `/newbot`.
3. Type a name, for example `My Builds`.
4. Type a username that ends with `bot`, for example `myname_builds_bot`.
5. BotFather sends you a long code like `123456789:AAH...`. This is your **bot token**.

Paste the token in the chat with Claude. Claude checks it with Telegram and says "Your bot @myname_builds_bot is working."

Do not want to paste it in the chat? Open the file `~/.config/tossfile/.env`, put the token after `TG_BOT_TOKEN=`, save, and tell Claude "done".

### Step 2: Connect your chat

Claude gives you a link. Open it on your phone and tap **Start**.

Your bot writes "Connected" in Telegram. That's all.

Want files in a group? Ask Claude for the group link. Open it and pick the group.

### Step 3: Send files

Just ask Claude:

- "send the apk to telegram"
- "send dist/app.zip to my phone"
- "kirim apk ke telegram"

With no file name, Claude finds the newest build in your project. It adds a short note with the app version and git commit.

## Files over 50 MB

With only the bot token, a file can be up to **50 MB**. This is a Telegram rule for bots.

For bigger files, up to **2000 MB**, you need two more values. Claude asks for them only when a file is too big. You get them once:

1. Go to https://my.telegram.org and log in with your phone number. The login code comes in your Telegram app, not by SMS.
2. Tap **API development tools**.
3. Fill in the form. App title and short name can be anything, like `tossfile`. Platform: Desktop.
4. Tap **Create application**.
5. Copy **App api_id** (only numbers) and **App api_hash** (32 letters and numbers).
6. Paste both in the chat with Claude.

Sometimes my.telegram.org shows only "ERROR". This is common. Try again later, try another browser, or turn off your VPN. Files under 50 MB still work while you wait.

## Things you can say later

| You say | What happens |
| :-- | :-- |
| "send the apk to telegram" | Sends the newest build |
| "send report.pdf to telegram" | Sends that file |
| "send it to my group" | Gives you a link to connect a group |
| "change my bot" | Uses a new bot token, then connects your chat again |
| "is tossfile set up?" | Claude checks and tells you what is missing |

## Where your keys are

Everything is in one file on your computer: `~/.config/tossfile/.env`

- It is outside your projects, so git does not pick it up.
- Only your user can read it.
- Claude never shows the values in the chat.

If you paste a token in the chat, it is part of that chat history. If you do not want that, put it in the file yourself (see Step 1).

To remove Tossfile setup completely, delete the folder `~/.config/tossfile`.

## If something goes wrong

Claude tells you the problem in plain words. The common ones:

| Problem | What to do |
| :-- | :-- |
| "This does not look like a bot token" | Copy the whole token from BotFather. It has a colon `:` in the middle. |
| "Telegram does not accept this bot token" | The token was changed. Send `/token` to @BotFather, pick your bot, paste the new token. |
| "Nobody pressed Start" | Open the link again and tap Start. Then tell Claude. |
| "The bot cannot write to the chat" | You blocked the bot or removed it from the group. Connect the chat again. |
| "File is over 50 MB" | Add api_id and api_hash (see "Files over 50 MB"). |
| "Could not reach Telegram" | Check the internet. Some networks and cloud sandboxes block Telegram. |
| "Install Certificates.command" | On a Mac with Python from python.org: open Applications, open the Python folder, double-click `Install Certificates.command`. |

## Someone has your bot token?

Send `/revoke` to @BotFather and pick your bot. The old token stops working, and BotFather gives you a new one. Tell Claude "change my bot token" and paste it. Your chat stays connected.
