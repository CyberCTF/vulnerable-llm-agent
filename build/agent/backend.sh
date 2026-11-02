# Sourced by start.sh (and by the lab's solve check): which model the agent talks to.
# With an OpenAI key (OPENAI_API_KEY in the environment, or the file /run/lab/openai_api_key) the
# agent calls OpenAI's gpt-4o, as upstream does; the lab network then needs internet access.
# Without one (the default) it talks to the local stand-in model (standin/server.py) on
# 127.0.0.1:8000, through the same OpenAI API: no key, no internet. STANDIN=1 in that case.
key="${OPENAI_API_KEY:-}"
if [ -z "$key" ] && [ -s /run/lab/openai_api_key ]; then
  key=$(tr -d '\r\n' < /run/lab/openai_api_key)
fi
if [ -n "$key" ]; then
  export OPENAI_API_KEY="$key"; STANDIN=0
else
  export OPENAI_API_KEY=stand-in OPENAI_API_BASE=http://127.0.0.1:8000/v1; STANDIN=1
fi
unset key
