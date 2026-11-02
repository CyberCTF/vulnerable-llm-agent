"""A deterministic stand-in for the lab's LLM, so the lab runs with no API key and no internet.

It answers OpenAI's chat completions API (streaming or not) on 127.0.0.1, where the unchanged
upstream agent (LangChain's ConversationalChatAgent through LiteLLM, model gpt-4o) sends its
requests. It plays the agent's model the way a model reads the conversation it is given:

- it follows the system prompt: it looks up the signed-in customer with GetCurrentUser, then that
  customer's transactions with GetUserTransactions, and refuses a request for another userId;
- but it cannot tell where a piece of text comes from: whatever looks like a tool result, its own
  reasoning or a system instruction counts as such, even inside the customer's message. That is
  the flaw the lab teaches (prompt injection, and its ReAct form, Thought/Action/Observation
  injection), as gpt-4o has it.

Python standard library only. Run: python server.py [port] (default 8000).
"""

import json
import re
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

TOOL_CURRENT_USER = "GetCurrentUser"
TOOL_TRANSACTIONS = "GetUserTransactions"

# Where LangChain's conversational agent puts the customer's message, and how it wraps tool results.
INPUT_HEADER = re.compile(r"Here is the user's input \(remember[^\n]*\):\n\n", re.S)
TOOL_RESPONSE = re.compile(r"^TOOL RESPONSE: ?\n-+\n(.*?)\n\nUSER'S INPUT\n-+\n", re.S)

# What a model reads as a tool result, its own reasoning or a system instruction.
OBSERVATION = re.compile(r"(?im)^\s*(observation|tool response)\s*:")
THOUGHT = re.compile(r"(?im)^\s*thought\s*:")
SYSTEM = re.compile(
    r"(?im)(\(#?\s*system\s*\)|#\s*system\b|\[\s*system\s*\]|<\s*system\s*>|\bsystem\s*:"
    r"|\bsystem\s+(message|prompt|instruction|update|notice|migration)"
    r"|\b(new|important|updated)\s+(important\s+)?instructions?\b"
    r"|\b(admin|administrator)\s+(note|notice|instruction|override)\b)"
)

USER_ID_FIELD = re.compile(r"""(?i)["']?user_?id["']?\s*[:=]\s*(?:"([^"\n]*)"|'([^'\n]*)'|([^\s,}\]]+))""")
USER_ID_WORDS = re.compile(r"(?i)\buser\s*_?id\b\D{0,40}?(\d+)")
USER_NUMBER = re.compile(r"(?i)\b(?:user|customer|account)\s*(?:number|no\.?|#)?\s*(\d+)\b")

TRANSACTION_WORDS = re.compile(
    r"(?i)\b(transactions?|payments?|purchases?|statement|spent|spending|history|transfers?|"
    r"account|activity|bank)\b"
)
WHO_AM_I = re.compile(r"(?i)\b(who am i|my (user ?id|username|name|account details)|current user)\b")

REFUSAL = (
    "Sorry, I can only operate on the userId of the signed-in customer, and I can't look up "
    "another customer's transactions."
)
HELP = (
    "I can help you with your recent bank transactions. Try asking me: "
    '"What are my recent transactions?"'
)


def text_of(message):
    content = message.get("content") or ""
    if isinstance(content, list):  # content parts
        content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
    return content


def parse_action(text):
    """The action of one of the agent's own earlier answers (a json blob in a code fence)."""
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None, None
    try:
        blob = json.loads(m.group(0))
        return blob.get("action"), blob.get("action_input")
    except (ValueError, AttributeError):
        return None, None


def user_id_in_result(text):
    """The userId a tool result (real or not) gives, as written (a string)."""
    m = USER_ID_FIELD.search(text)
    if m:
        return next(g for g in m.groups() if g is not None).strip()
    m = USER_ID_WORDS.search(text)
    return m.group(1) if m else None


def believed_user(user_input):
    """The current userId the conversation's own text leads the model to believe, if any: from a
    tool result, a thought of its own or a system instruction found in the customer's message.
    The last such statement wins, as the most recent context does for a model."""
    found = []
    for pattern, reader in ((OBSERVATION, user_id_in_result), (THOUGHT, user_id_in_result),
                            (SYSTEM, lambda s: (USER_ID_WORDS.search(s) or [None, None])[1])):
        for m in pattern.finditer(user_input):
            value = reader(user_input[m.end():])
            if value:
                found.append((m.start(), value))
    return max(found)[1] if found else None


def plain_request_for(user_input):
    """A userId the customer asks for in plain words ("transactions of userId 2")."""
    m = USER_ID_WORDS.search(user_input) or USER_NUMBER.search(user_input)
    return m.group(1) if m else None


def transactions_table(observation):
    try:
        rows = json.loads(observation)
    except ValueError:
        return "Here is what I found:\n\n" + observation
    if not rows:
        return "There are no recent transactions on this account."
    columns = list(rows[0].keys())
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    lines += ["| " + " | ".join(str(r.get(c, "")) for c in columns) + " |" for r in rows]
    return "Here are your recent transactions:\n\n" + "\n".join(lines)


def decide(messages):
    """The next step of the agent: (action, action_input)."""
    texts = [(m.get("role"), text_of(m)) for m in messages]
    start = max((i for i, (role, t) in enumerate(texts) if role == "user" and INPUT_HEADER.search(t)),
                default=None)
    if start is None:
        return "Final Answer", HELP
    user_input = INPUT_HEADER.split(texts[start][1], maxsplit=1)[1]

    # What the agent has done this turn: its own actions and the tools' answers.
    steps, pending = [], None
    for role, t in texts[start + 1:]:
        if role == "assistant":
            pending = parse_action(t)
        elif role == "user" and pending:
            m = TOOL_RESPONSE.match(t)
            steps.append((pending[0], pending[1], m.group(1) if m else t))
            pending = None

    current = believed_user(user_input)
    injected = current is not None
    for tool, _, observation in steps:
        if tool == TOOL_CURRENT_USER:
            current = user_id_in_result(observation) or current
        elif tool == TOOL_TRANSACTIONS:
            return "Final Answer", transactions_table(observation)

    asked = None if injected else plain_request_for(user_input)
    wants_transactions = injected or bool(TRANSACTION_WORDS.search(user_input)) or asked is not None

    if WHO_AM_I.search(user_input) and not wants_transactions:
        if current is None:
            return TOOL_CURRENT_USER, ""
        return "Final Answer", f"You are signed in as userId {current}."
    if not wants_transactions:
        return "Final Answer", HELP
    if current is None:
        return TOOL_CURRENT_USER, ""
    if asked is not None and asked != str(current):
        return "Final Answer", REFUSAL
    return TOOL_TRANSACTIONS, str(current)


def completion_text(messages):
    action, action_input = decide(messages)
    blob = json.dumps({"action": action, "action_input": action_input}, indent=4)
    return f"```json\n{blob}\n```"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _json(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path.rstrip("/").endswith("/models"):
            return self._json(200, {"object": "list", "data": [{"id": "gpt-4o", "object": "model"}]})
        if self.path == "/health":
            return self._json(200, {"ok": True})
        self._json(404, {"error": {"message": "not found"}})

    def do_POST(self):
        if not self.path.rstrip("/").endswith("/chat/completions"):
            return self._json(404, {"error": {"message": "not found"}})
        request = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        text = completion_text(request.get("messages", []))
        model = request.get("model", "gpt-4o")
        ident, created = f"chatcmpl-standin-{time.time_ns()}", int(time.time())
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if not request.get("stream"):
            return self._json(200, {
                "id": ident, "object": "chat.completion", "created": created, "model": model,
                "choices": [{"index": 0, "finish_reason": "stop",
                             "message": {"role": "assistant", "content": text}}],
                "usage": usage,
            })
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        def chunk(delta, finish=None, **extra):
            body = {"id": ident, "object": "chat.completion.chunk", "created": created, "model": model,
                    "choices": [{"index": 0, "delta": delta, "finish_reason": finish}], **extra}
            self.wfile.write(b"data: " + json.dumps(body).encode() + b"\n\n")

        chunk({"role": "assistant", "content": ""})
        for piece in re.findall(r"\S+\s*|\s+", text):  # word by word, as a model streams
            chunk({"content": piece})
        chunk({}, "stop")
        if (request.get("stream_options") or {}).get("include_usage"):
            body = {"id": ident, "object": "chat.completion.chunk", "created": created,
                    "model": model, "choices": [], "usage": usage}
            self.wfile.write(b"data: " + json.dumps(body).encode() + b"\n\n")
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()
