# Damn Vulnerable LLM Agent

[Damn Vulnerable LLM Agent](https://github.com/ReversecLabs/damn-vulnerable-llm-agent) by
WithSecure Labs (now ReversecLabs): a chatbot built on a LangChain ReAct agent that fetches the
current user's bank transactions through tools, to learn prompt injection and
Thought/Action/Observation injection against LLM agents. It was first a challenge of the BSides
London 2023 CTF. This repository runs it with [Isoloom](https://www.isoloom.com):
[`isoloom.yml`](isoloom.yml) describes the machine, and the upstream source in
[`build/agent/app/`](build/agent/app) builds with its own Dockerfile, with the dependencies
pinned by date. It runs on its own: no API key, no internet.

| Machine | Service |
| --- | --- |
| agent | Streamlit chatbot on port 8501 |

## Run it

No key and no internet needed: the agent's model is a local, deterministic stand-in
([`build/agent/standin/server.py`](build/agent/standin/server.py)) that answers OpenAI's chat API
inside the machine, and the lab network has no internet access.

```bash
isoloom generate
isoloom run docker
```

Then open http://localhost:8501/ and ask for your recent transactions. The same spec runs as
Docker on a local VM (`docker-vm`), on a cloud VM (`cloud-docker`) or on Kubernetes. Lab guide:
WithSecure's [publication](https://labs.withsecure.com/publications/llm-agent-prompt-injection)
on ReAct agent prompt injection and the
[project README](https://github.com/ReversecLabs/damn-vulnerable-llm-agent#readme) (it includes
the solutions).

### The model

Upstream's agent (LangChain's conversational ReAct agent, unchanged) asks a model, in each
step, which tool to call or what to answer. Small local models were measured for that role on
CPU (Qwen2.5 3B Instruct, Llama 3.2 3B, Qwen2.5 7B Instruct, through Ollama): the 3B models
break the agent's JSON format and Qwen2.5 3B even hands over userId 2's transactions to a plain
request; the 7B one needs about 5 GB of RAM and up to 80 s an answer, and solved only one of the
two intended attacks. So the stand-in plays the model instead. It follows the system prompt (look
up the signed-in customer, fetch their transactions, refuse any other userId) but trusts
whatever in the conversation looks like a tool result, its own reasoning or a system
instruction, the customer's message included: the prompt injection and Thought/Action/
Observation injection that upstream teaches solve it, a plain request for another userId does
not.

To play it on OpenAI's gpt-4o instead, as upstream does, give the agent a key: set
`OPENAI_API_KEY` in its environment, or add an `OPENAI_API_KEY` input to `isoloom.yml` written to
`/run/lab/openai_api_key` (as `CTF_FLAG_MAIN` is). The lab network then needs
`internet: true`. Without a key the stand-in answers.

### Checks

`isothrum check` proves that the app answers, that the machine has no internet, and that the
lab is solvable: [`build/agent/check/solve.sh`](build/agent/check/solve.sh) replays upstream's
README solutions through the real app and expects userId 2's transactions (the flag) to show,
and a plain request for them to be refused.

Upstream version and commit: [UPSTREAM.md](UPSTREAM.md).

## Licence

Apache-2.0, as Damn Vulnerable LLM Agent ([LICENSE](LICENSE)). This application is deliberately
vulnerable: keep it isolated (and, with an OpenAI key, use one with a spending limit).
