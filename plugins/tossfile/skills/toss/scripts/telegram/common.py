"""Shared helpers: config loading and a self-managed virtualenv with Telethon."""
import os
import subprocess
import sys
from pathlib import Path

CONFIG_DIR = Path(
    os.environ.get("TOSSFILE_HOME") or Path.home() / ".config" / "tossfile"
)
ENV_FILE = CONFIG_DIR / ".env"
VENV_DIR = CONFIG_DIR / "venv"
SESSION = str(CONFIG_DIR / "bot")  # Telethon adds ".session"

KEYS = ["TG_API_ID", "TG_API_HASH", "TG_BOT_TOKEN", "TG_CHAT_ID"]

TEMPLATE = """# Tossfile - keep this file private, never commit it.
# api_id and api_hash: https://my.telegram.org -> API development tools
TG_API_ID=
TG_API_HASH=
# Bot token from @BotFather
TG_BOT_TOKEN=
# Filled in automatically by get_chat_id.py
TG_CHAT_ID=
"""


def fail(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def _venv_python():
    sub = "Scripts/python.exe" if os.name == "nt" else "bin/python"
    return VENV_DIR / sub


def ensure_telethon():
    """Import Telethon; if missing, build a private venv and re-run this script in it."""
    try:
        import telethon  # noqa: F401
        return
    except ImportError:
        pass
    if os.environ.get("TOSSFILE_BOOTSTRAPPED") == "1":
        fail("Telethon could not be installed. Run: pip install telethon")
    py = _venv_python()
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not py.exists():
        print("First run: creating a private Python environment...", flush=True)
        import venv
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)
    have = subprocess.run([str(py), "-c", "import telethon"], capture_output=True)
    if have.returncode != 0:
        print("Installing Telethon...", flush=True)
        r = subprocess.run([str(py), "-m", "pip", "install", "--quiet", "telethon"])
        if r.returncode != 0:
            fail("pip could not install Telethon (check the internet connection).")
    env = dict(os.environ, TOSSFILE_BOOTSTRAPPED="1")
    sys.exit(subprocess.call([str(py)] + sys.argv, env=env))


def read_env():
    values = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip().strip('"').strip("'")
    # Real environment variables win over the file.
    for k in KEYS:
        if os.environ.get(k):
            values[k] = os.environ[k]
    return values


def write_env_value(key, value):
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines() if ENV_FILE.exists() else []
    out, done = [], False
    for line in lines:
        if line.strip().startswith(f"{key}="):
            out.append(f"{key}={value}")
            done = True
        else:
            out.append(line)
    if not done:
        out.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")


def load_config(need_chat=True):
    cfg = read_env()
    need = [k for k in KEYS if need_chat or k != "TG_CHAT_ID"]
    missing = [k for k in need if not cfg.get(k)]
    if missing:
        print(f"SETUP_NEEDED: missing {', '.join(missing)} in {ENV_FILE}", file=sys.stderr)
        sys.exit(2)
    try:
        cfg["TG_API_ID"] = int(cfg["TG_API_ID"])
    except ValueError:
        fail("TG_API_ID must be a number.")
    return cfg


def parse_chat(value):
    value = str(value).strip()
    try:
        return int(value)
    except ValueError:
        return value  # @username or channel link


def make_client(cfg):
    from telethon import TelegramClient
    return TelegramClient(
        SESSION, cfg["TG_API_ID"], cfg["TG_API_HASH"],
        connection_retries=3, retry_delay=2, timeout=20,
    )


async def start_bot(client, cfg, timeout=45):
    """Log the bot in; give up with a clear message if Telegram is unreachable."""
    import asyncio
    try:
        await asyncio.wait_for(client.start(bot_token=cfg["TG_BOT_TOKEN"]), timeout)
    except asyncio.TimeoutError:
        fail(f"ConnectionError: could not reach Telegram within {timeout}s from this machine.")
