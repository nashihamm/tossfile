# Tossfile

Tosses build files (APK, AAB, zip, anything up to 2 GB) from Claude to your phone, so you do not drag and drop them by hand. Delivers to your Telegram chat through your own bot today; more destinations are planned.

## Install

```
/plugin install tossfile --marketplace YOUR_GITHUB_USERNAME/tossfile
```

## Use

Say "send the apk to telegram" (or "kirim apk ke telegram") after a build, or run `/tossfile:toss path/to/file`.

## One-time setup

Say "set up tossfile". Claude walks you through it in the chat, about 2 minutes:

1. Make a bot with @BotFather and paste the token.
2. Open the link Claude gives you and tap **Start**.

Files up to 50 MB work with that. For files up to 2 GB, Claude asks for `api_id` and `api_hash` from https://my.telegram.org when you first need them.

Keys are stored in `~/.config/tossfile/.env` on your computer, outside your projects, so they cannot be committed to git by accident.

Full guide in simple English: `GUIDE.md` in the repository.

## Requirements

Python 3.8+ and internet access to Telegram on the machine where the build file is. Nothing to install for files up to 50 MB; Telethon installs itself into a private environment the first time you send a bigger file.
