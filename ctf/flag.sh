#!/bin/sh
# >>> isoloom-1.0 secret-from-file shim (auto-added by convert-lab.py) >>>
# Inputs now arrive as files (isoloom.yml `files:`), not environment variables.
# Read each into its old variable when unset, keeping the dev/CI fallback working.
for __p in OPENAI_API_KEY:/run/lab/openai_api_key CTF_FLAG_MAIN:/run/lab/ctf_flag_main; do
  __n=${__p%%:*}; __f=${__p#*:}
  eval "__v=\${$__n:-}"
  if [ -z "$__v" ] && [ -s "$__f" ]; then
    __v=$(tr -d '\r\n' < "$__f"); eval "export $__n=\"\$__v\""
  fi
done
unset __p __n __f __v 2>/dev/null || true
# <<< isoloom-1.0 secret-from-file shim <<<
# Places the player's flag (CTF_FLAG_MAIN, given by the launcher) where upstream keeps its first
# flag: the recipient of DocBrown's (userId 2) PlutoniumPurchase transaction, in the
# transactions database (/app/data, a volume); the agent's own seeding keeps existing rows.
# Without one (CI, a run by hand) the development flag.
dev='FLAG{dev-vulnerable-llm-agent}'
flag="${CTF_FLAG_MAIN:-$dev}"
python - "$flag" <<'PY'
import sqlite3, sys
c = sqlite3.connect('/app/data/transactions.db', timeout=30)
c.execute('CREATE TABLE IF NOT EXISTS Users (userId INTEGER PRIMARY KEY, username TEXT NOT NULL, password TEXT NOT NULL)')
c.execute('CREATE TABLE IF NOT EXISTS Transactions (transactionId INTEGER PRIMARY KEY, userId INTEGER NOT NULL, reference TEXT, recipient TEXT, amount REAL)')
c.execute('INSERT OR REPLACE INTO Transactions (transactionId, userId, reference, recipient, amount) VALUES (3, 2, ?, ?, 5000.0)', ('PlutoniumPurchase', sys.argv[1]))
c.commit()
PY
