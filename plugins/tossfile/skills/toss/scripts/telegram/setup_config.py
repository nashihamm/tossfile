#!/usr/bin/env python3
"""Create the private config file if needed and say what the next setup step is.
Never prints secret values.

STATUS lines:
  need_token  -> ask the user for a bot token (save_config.py)
  need_chat   -> connect a chat (get_chat_id.py prepare, then wait)
  ready       -> files can be sent; LIMIT says how big
"""
from common import ENV_FILE, KEYS, ensure_config_file, has_big_file_keys, read_env

created = ensure_config_file()
print(f"{'Created config file' if created else 'Config file'}: {ENV_FILE}")

cfg = read_env()
for k in KEYS:
    print(f"  {k}: {'set' if cfg.get(k) else 'empty'}")

if has_big_file_keys(cfg):
    print("LIMIT: 2000 MB per file")
else:
    print("LIMIT: 50 MB per file (add TG_API_ID and TG_API_HASH for up to 2000 MB)")

if not cfg.get("TG_BOT_TOKEN"):
    print("STATUS: need_token")
elif not cfg.get("TG_CHAT_ID"):
    print("STATUS: need_chat")
else:
    print("STATUS: ready")
