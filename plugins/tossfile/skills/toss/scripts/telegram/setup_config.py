#!/usr/bin/env python3
"""Create the private config file if needed and report which values are still empty.
Never prints secret values."""
import os
from common import CONFIG_DIR, ENV_FILE, KEYS, TEMPLATE, read_env

CONFIG_DIR.mkdir(parents=True, exist_ok=True)
if not ENV_FILE.exists():
    ENV_FILE.write_text(TEMPLATE, encoding="utf-8")
    try:
        os.chmod(ENV_FILE, 0o600)
    except OSError:
        pass
    print(f"Created config file: {ENV_FILE}")
else:
    print(f"Config file: {ENV_FILE}")

cfg = read_env()
for k in KEYS:
    print(f"  {k}: {'set' if cfg.get(k) else 'EMPTY'}")
missing = [k for k in KEYS if not cfg.get(k)]
if not missing:
    print("STATUS: ready")
elif missing == ["TG_CHAT_ID"]:
    print("STATUS: run get_chat_id.py next")
else:
    print("STATUS: the user must fill in the EMPTY values (except TG_CHAT_ID)")
