# Tossfile

A Claude plugin that tosses build files from your computer to your phone. Today it delivers to Telegram; more destinations are planned. After Claude builds an APK, say "send the apk to telegram" and it arrives on your phone. No drag and drop.

- Works with any file: APK, AAB, IPA, zip, PDF.
- Files up to 2 GB. The plugin logs in as your bot over MTProto (Telethon), so the 50 MB limit of the HTTP Bot API does not apply.
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

## One-time setup (about 5 minutes)

You need three values:

| Value | Where to get it |
| :-- | :-- |
| `TG_BOT_TOKEN` | Open @BotFather in Telegram, send `/newbot`, copy the token |
| `TG_API_ID` | Sign in at https://my.telegram.org, open "API development tools", create an app |
| `TG_API_HASH` | Same page as `TG_API_ID` |

Create the config file and paste them in:

```bash
mkdir -p ~/.config/tossfile
nano ~/.config/tossfile/.env
```

```
TG_API_ID=
TG_API_HASH=
TG_BOT_TOKEN=
TG_CHAT_ID=
```

Leave `TG_CHAT_ID` empty. The first time you use the plugin, Claude asks you to send one message to your bot and saves the chat ID for you. To deliver into a group, add the bot to the group and send the message there.

## Use

Just ask:

- "send the apk to telegram"
- "kirim apk ke telegram"
- "send dist/report.zip to my phone"

Or run the skill directly: `/tossfile:toss path/to/file`

With no path, Claude looks for the newest build in `android/app/build/outputs/` (Capacitor and native Android projects) and adds a short caption with the app version and git commit.

## Requirements

- Python 3.8 or newer.
- Internet access to Telegram from the machine that runs Claude. Telethon is installed automatically into a private environment in `~/.config/tossfile/venv` on first run.

## Security

- Keys live in `~/.config/tossfile/.env`, outside your projects, so they cannot be committed by accident.
- The plugin never prints your keys.
- A leaked bot token lets someone send messages as your bot. If that happens, send `/revoke` to @BotFather to get a new one.

## Troubleshooting

| Message | Fix |
| :-- | :-- |
| `SETUP_NEEDED` | A value is missing in the `.env` file |
| `AccessTokenInvalidError`, `ApiIdInvalidError` | A key was copied wrong |
| `Could not find the input entity` | Open your bot in Telegram, press Start, then ask Claude to set up the chat again |
| `ConnectionError` | This machine cannot reach Telegram (cloud sandbox, firewall, or blocked network) |

## Roadmap

Telegram is the first destination. Each destination lives in its own folder under `skills/toss/scripts/`, so adding one (email link, WhatsApp, Discord) does not touch the others. Pull requests are welcome.

## License

MIT
