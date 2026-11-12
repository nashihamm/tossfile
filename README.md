# Tossfile

A Claude plugin that tosses build files from your computer to your phone. Today it delivers to Telegram; more destinations are planned. After Claude builds an APK, say "send the apk to telegram" and it arrives on your phone. No drag and drop.

- Works with any file: APK, AAB, IPA, zip, PDF.
- Files up to 50 MB with only a bot token. Up to 2 GB when you add `api_id` and `api_hash`: big files go over MTProto (Telethon), which does not have the 50 MB limit of the HTTP Bot API.
- You use your own bot and your own keys. Nothing is sent to anyone else.

## Install

In Claude Code:

```
/plugin install tossfile --marketplace YOUR_GITHUB_USERNAME/tossfile
```

That one-step form needs Claude Code 2.1.275 or later. On older versions, use two steps:

```
/plugin marketplace add YOUR_GITHUB_USERNAME/tossfile
/plugin install tossfile@nashihamm-plugins
```

Or from a shell:

```bash
claude plugin marketplace add YOUR_GITHUB_USERNAME/tossfile
claude plugin install tossfile@nashihamm-plugins
```

## One-time setup (about 2 minutes)

Say to Claude: **"set up tossfile"**. Claude walks you through it in the chat:

1. Make a bot with @BotFather (`/newbot`) and paste the token in the chat.
2. Open the link Claude gives you and tap **Start**.

That's all. Files up to 50 MB work now. For bigger files (up to 2 GB), Claude asks for `api_id` and `api_hash` from https://my.telegram.org the first time a file is too big.

Read [GUIDE.md](GUIDE.md) for every step in simple English.

## Use

Just ask:

- "send the apk to telegram"
- "kirim apk ke telegram"
- "send dist/report.zip to my phone"

Or run the skill directly: `/tossfile:toss path/to/file`

With no path, Claude looks for the newest build in `android/app/build/outputs/` (Capacitor and native Android projects) and adds a short caption with the app version and git commit.

## Requirements

- Python 3.8 or newer.
- Internet access to Telegram from the machine that runs Claude.
- Nothing to install for files up to 50 MB. For bigger files, Telethon installs itself into a private environment in `~/.config/tossfile/venv` the first time.

## Security

- Keys live in `~/.config/tossfile/.env`, outside your projects, so they cannot be committed by accident.
- The plugin never prints your keys. Values you paste in the chat are saved through stdin, not the command line.
- Connecting a chat uses a one-time code in the Start link, so a stranger writing to your bot at the same moment cannot take it.
- A leaked bot token lets someone send messages as your bot. If that happens, send `/revoke` to @BotFather to get a new one.

## Troubleshooting

Claude explains errors in plain words. See the table in [GUIDE.md](GUIDE.md#if-something-goes-wrong).

## Roadmap

Telegram is the first destination. Each destination lives in its own folder under `skills/toss/scripts/`, so adding one (email link, WhatsApp, Discord) does not touch the others. Pull requests are welcome.

## License

MIT
