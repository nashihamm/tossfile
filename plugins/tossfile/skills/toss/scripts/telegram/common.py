"""Shared helpers: config file, the HTTP Bot API, and a self-managed virtualenv with Telethon.

Only the bot token and the chat id are required. The HTTP Bot API carries files up
to 50 MB with nothing else. api_id and api_hash are optional: with them, bigger
files (up to 2000 MB) go over MTProto through Telethon.
"""
import json
import os
import re
import ssl
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

CONFIG_DIR = Path(
    os.environ.get("TOSSFILE_HOME") or Path.home() / ".config" / "tossfile"
)
ENV_FILE = CONFIG_DIR / ".env"
VENV_DIR = CONFIG_DIR / "venv"
SESSION = str(CONFIG_DIR / "bot")  # Telethon adds ".session"
PENDING_FILE = CONFIG_DIR / "pending_connect.json"

REQUIRED = ["TG_BOT_TOKEN", "TG_CHAT_ID"]
OPTIONAL = ["TG_API_ID", "TG_API_HASH"]
KEYS = ["TG_BOT_TOKEN", "TG_CHAT_ID", "TG_API_ID", "TG_API_HASH"]

HTTP_LIMIT = 50 * 1000 * 1000  # Bot API sendDocument limit, with a small margin
MTPROTO_LIMIT = 2000 * 1024 * 1024

TOKEN_RE = re.compile(r"^\d{5,}:[A-Za-z0-9_-]{30,}$")
API_HASH_RE = re.compile(r"^[0-9a-f]{32}$")

TEMPLATE = """# Tossfile - keep this file private, never commit it.
# Required. Bot token from @BotFather (/newbot).
TG_BOT_TOKEN=
# Required. Filled in automatically when you connect your chat.
TG_CHAT_ID=
# Optional. Only needed for files bigger than 50 MB (up to 2000 MB).
# Get both at https://my.telegram.org -> API development tools.
TG_API_ID=
TG_API_HASH=
"""


def fail(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def ensure_config_file():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    created = False
    if not ENV_FILE.exists():
        ENV_FILE.write_text(TEMPLATE, encoding="utf-8")
        created = True
    try:
        os.chmod(ENV_FILE, 0o600)
    except OSError:
        pass
    return created


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
    ensure_config_file()
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
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


def has_big_file_keys(cfg):
    return bool(cfg.get("TG_API_ID") and cfg.get("TG_API_HASH"))


def load_config(need_chat=True, need_api=False):
    cfg = read_env()
    need = [k for k in REQUIRED if need_chat or k != "TG_CHAT_ID"]
    if need_api:
        need += OPTIONAL
    missing = [k for k in need if not cfg.get(k)]
    if missing:
        print(f"SETUP_NEEDED: missing {', '.join(missing)} in {ENV_FILE}", file=sys.stderr)
        sys.exit(2)
    if cfg.get("TG_API_ID"):
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


# --- HTTP Bot API (standard library only) -------------------------------------

class BotApiError(Exception):
    pass


def _ssl_hint(e):
    if "CERTIFICATE_VERIFY_FAILED" in str(e):
        return (" Python cannot check HTTPS certificates. On macOS with python.org Python, "
                "run 'Install Certificates.command' in the Python folder under Applications.")
    return ""


def api_url(token, method):
    return f"https://api.telegram.org/bot{token}/{method}"


def bot_api(token, method, params=None, timeout=30):
    """Call a Bot API method with a JSON body and return its 'result'."""
    data = json.dumps(params or {}).encode()
    req = urllib.request.Request(
        api_url(token, method), data=data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read().decode())
        except ValueError:
            raise BotApiError(f"HTTP {e.code}") from None
    except (urllib.error.URLError, ssl.SSLError, TimeoutError, OSError) as e:
        reason = getattr(e, "reason", e)
        raise BotApiError(f"ConnectionError: could not reach Telegram ({reason}).{_ssl_hint(e)}") from None
    if not body.get("ok"):
        code = body.get("error_code")
        desc = body.get("description", "unknown error")
        if code == 401:
            raise BotApiError("TokenInvalid: Telegram does not accept this bot token.")
        if code == 429:
            wait = body.get("parameters", {}).get("retry_after", "?")
            raise BotApiError(f"FloodWait: Telegram asks to wait {wait} seconds.")
        raise BotApiError(f"{desc} (code {code})")
    return body["result"]


def check_token(token):
    """Return the bot's getMe result, or raise BotApiError with a plain reason."""
    if not TOKEN_RE.match(token):
        raise BotApiError(
            "TokenFormat: this does not look like a bot token. "
            "It looks like 123456789:AAH... (numbers, a colon, then about 35 letters)."
        )
    return bot_api(token, "getMe")


# --- Telethon (only for files over 50 MB) -------------------------------------

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
        print("First big file: creating a private Python environment...", flush=True)
        import venv
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)
    have = subprocess.run([str(py), "-c", "import telethon"], capture_output=True)
    if have.returncode != 0:
        print("Installing Telethon (one time only)...", flush=True)
        r = subprocess.run([str(py), "-m", "pip", "install", "--quiet", "telethon"])
        if r.returncode != 0:
            fail("pip could not install Telethon (check the internet connection).")
    env = dict(os.environ, TOSSFILE_BOOTSTRAPPED="1")
    sys.exit(subprocess.call([str(py)] + sys.argv, env=env))


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
