# Tossfile

An agent skill that tosses files from your computer to your phone. Ask your AI coding agent to send a file and it arrives on your phone in seconds. No cable, no drag and drop, no emailing yourself. Today it delivers to Telegram; more destinations are planned.

Works with any agent that can read a skill and run a shell command: Claude Code, Codex, Gemini CLI, Cursor, GitHub Copilot, and others. The skill is a plain `SKILL.md` plus small Python scripts, with nothing tied to one agent.

**Built for app builds.** Right after your agent builds your app, say "send the build to my phone". Tossfile finds the newest APK or AAB on its own (Flutter, Capacitor, native Android) and adds a caption with the app name, version, build type, and git commit, so you always know which build you are installing.

**Works for any other file too.** Reports, exports, screenshots, logs, zips, PDFs, videos: anything on your computer that you want on your phone.

- Any file type, several files at once.
- Files up to 50 MB with only a bot token. Up to 2 GB when you add `api_id` and `api_hash`: big files go over MTProto (Telethon), which does not have the 50 MB limit of the HTTP Bot API.
- You use your own bot and your own keys. Nothing is sent to anyone else.

## Install

### Claude Code

Tossfile ships as a Claude Code plugin:

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

### Other agents

The skill lives in [`plugins/tossfile/skills/toss/`](plugins/tossfile/skills/toss/). Copy that whole folder (keep `scripts/` next to `SKILL.md`) into the folder where your agent loads skills. Check your agent's docs for the exact location.

Agent has no skills support? Point it at the file instead, for example in `AGENTS.md`: "To send a file to my phone, follow `path/to/toss/SKILL.md`."

## One-time setup (about 2 minutes)

Say to your agent: **"set up tossfile"**. It walks you through it in the chat:

1. Make a bot with @BotFather (`/newbot`) and paste the token in the chat.
2. Open the link your agent gives you and tap **Start**.

That's all. Files up to 50 MB work now. For bigger files (up to 2 GB), your agent asks for `api_id` and `api_hash` from https://my.telegram.org the first time a file is too big.

Read [GUIDE.md](GUIDE.md) for every step in simple English.

## Use

Just ask. Some examples:

**App builds**

- "build the release apk and send it to my phone"
- "send the apk to telegram"
- "kirim apk ke telegram"

With no path, your agent looks for the newest build output in the project:

| Project | Where it looks |
| --- | --- |
| Flutter | `build/app/outputs/flutter-apk/`, `build/app/outputs/bundle/` |
| Capacitor / native Android | `android/app/build/outputs/apk/`, `android/app/build/outputs/bundle/` |
| Anything else | the newest `*.apk` in the project |

The caption shows the app name, version, debug or release, branch, and short commit.

**Any other file**

- "send dist/report.zip to my phone"
- "toss the screenshots in ./out to telegram"
- "kirim file invoice.pdf ke hp"

In Claude Code you can also run the skill directly: `/tossfile:toss path/to/file`

## Requirements

- Python 3.8 or newer.
- Internet access to Telegram from the machine that runs your agent. Cloud sandboxes often block it, so run the agent on your own computer.
- Nothing to install for files up to 50 MB. For bigger files, Telethon installs itself into a private environment in `~/.config/tossfile/venv` the first time.

## Security

- Keys live in `~/.config/tossfile/.env`, outside your projects, so they cannot be committed by accident.
- The scripts never print your keys. Values you paste in the chat are saved through stdin, not the command line.
- Connecting a chat uses a one-time code in the Start link, so a stranger writing to your bot at the same moment cannot take it.
- A leaked bot token lets someone send messages as your bot. If that happens, send `/revoke` to @BotFather to get a new one.

## Troubleshooting

Your agent explains errors in plain words. See the table in [GUIDE.md](GUIDE.md#if-something-goes-wrong).

## Roadmap

Telegram is the first destination. Each destination lives in its own folder under `skills/toss/scripts/`, so adding one (email link, WhatsApp, Discord) does not touch the others. Pull requests are welcome.

## License

MIT
