# Tossfile

Tosses build files (APK, AAB, zip, anything up to 2 GB) from Claude to your phone, so you do not drag and drop them by hand. Delivers to your Telegram chat through your own bot today; more destinations are planned.

## Install

```
/plugin install tossfile --marketplace YOUR_GITHUB_USERNAME/tossfile
```

## Use

Say "send the apk to telegram" (or "kirim apk ke telegram") after a build, or run `/tossfile:toss path/to/file`.

## One-time setup

Claude walks you through it the first time. You need:

1. A bot token from @BotFather.
2. `api_id` and `api_hash` from https://my.telegram.org (API development tools).
3. One message from you to the bot, so it knows where to deliver.

Keys are stored in `~/.config/tossfile/.env` on your computer, outside your projects, so they cannot be committed to git by accident.

## Requirements

Python 3.8+ and internet access to Telegram on the machine where the build file is. Telethon is installed automatically into a private environment on first run.
