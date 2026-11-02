# Solution (instructors only)

Not player material: the lab page is built from `.ctf/metadata.json` and `.ctf/objectives.json`.

## Objective

Make the chatbot fetch userId 2's transactions. The flag (the player's `CTF_FLAG_MAIN`, planted
by `ctf/flag.sh`) is the recipient of their `PlutoniumPurchase` transaction.

## Intended solutions

Both are upstream's, word for word, in its README's "Possible Payload Solutions"
([`build/agent/app/README.md`](build/agent/app/README.md)); the solve check replays exactly those.

1. **Prompt injection.** The customer's message carries a system-style instruction that the
   current user's userId is now 2. The model can't tell it from its real system prompt, so it
   skips the GetCurrentUser lookup and calls GetUserTransactions with 2.
2. **Thought/Action/Observation injection.** The message carries a fake GetCurrentUser action
   and its observation (userId 2), followed by a fake thought. The agent takes them for steps it
   already ran, and goes on to fetch userId 2's transactions.

A plain request for userId 2's transactions is refused: the model first looks up the signed-in
customer (userId 1), then declines.

Upstream's second flag (DocBrown's password, through SQL injection in the userId the agent passes
to GetUserTransactions) is not a catalogue objective.

## Why it works, and the fix

The authorization decision ("only the signed-in customer's transactions") lives in the model's
prompt, and the model reads the customer's text in the same stream as its instructions and its
tool results. Nothing in the prompt can enforce it. The fix is in the tools:
GetUserTransactions should take the userId from the session, not from the model (or check it
against the session), so whatever the model is talked into, it only ever gets the signed-in
customer's rows. The tool should also use a parameterized query (`transaction_db.py` formats the
userId into the SQL), which closes upstream's second flag.

Detection: tool calls whose userId differs from the session's user, and customer messages
containing `Observation:`, `Thought:` or system-style markers.
