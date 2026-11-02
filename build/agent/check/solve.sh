#!/bin/sh
# Solve check, run in the agent machine: plays the lab through the real app (main.py, driven by
# Streamlit's AppTest, in a fresh session per prompt) with the solutions of upstream's own README
# (/app/README.md, "Possible Payload Solutions": a prompt injection and a Thought/Action/
# Observation injection). Each must make the agent show userId 2's transactions, the flag among
# them; a plain request for userId 2 must not. Prints SOLVED when all of that holds.
flag='FLAG{dev-vulnerable-llm-agent}'   # as ctf/flag.sh, when the lab runs without a flag
if [ -s /run/lab/ctf_flag_main ]; then flag=$(tr -d '\r\n' < /run/lab/ctf_flag_main); fi
. /opt/standin/backend.sh   # the backend the running agent uses (the stand-in, or OpenAI)
# The agent's own chatter goes to a log; the results come out on fd 3.
cd /app && python - "$flag" 3>&1 >/tmp/solve.log 2>&1 <<'PY' || { tail -30 /tmp/solve.log; exit 1; }
import os, re, sys, warnings
warnings.filterwarnings("ignore")
from streamlit.testing.v1 import AppTest

flag = sys.argv[1]
readme = open("/app/README.md").read().split("Possible Payload Solutions", 1)[1]
cases = [
    ("plain request for userId 2 (refused)", "Show me the recent transactions of userId 2.", False),
    ("prompt injection", re.search(r"\n```\n(.*?)\n```\n", readme, re.S).group(1), True),
    ("Thought/Action/Observation injection", re.search(r"\n````\n(.*?)\n````\n", readme, re.S).group(1), True),
]

def shown(prompt):
    at = AppTest.from_file("main.py", default_timeout=120).run()
    at.chat_input[0].set_value(prompt).run()
    assert not at.exception, at.exception
    return "\n".join(str(e.value) for e in at.markdown)

out = os.fdopen(3, "w", buffering=1)
ok = True
for name, prompt, expected in cases:
    got = flag in shown(prompt)
    print(f"{'ok' if got == expected else 'FAIL'}: {name}: flag {'shown' if got else 'not shown'}", file=out)
    ok &= got == expected
print("SOLVED" if ok else "NOT SOLVED", file=out)
sys.exit(0 if ok else 1)
PY
