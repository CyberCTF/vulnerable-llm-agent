#!/bin/sh
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
