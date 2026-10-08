# Damn Vulnerable LLM Agent

[Damn Vulnerable LLM Agent](https://github.com/ReversecLabs/damn-vulnerable-llm-agent) by
WithSecure Labs (now ReversecLabs): a chatbot built on a LangChain ReAct agent that fetches the
current user's bank transactions through tools, to learn prompt injection and
Thought/Action/Observation injection against LLM agents. It was first a challenge of the BSides
London 2023 CTF. This repository runs it with [Isoloom](https://www.isoloom.com):
[`isoloom.yml`](isoloom.yml) describes the machine, and the upstream source in
[`build/agent/app/`](build/agent/app) builds with its own Dockerfile, with the dependencies
pinned by date.

| Machine | Service |
| --- | --- |
| agent | Streamlit chatbot on port 8501 |

## Run it

The agent calls OpenAI (model `gpt-4o`), so it needs an API key, passed at launch as the
`OPENAI_API_KEY` input; the lab network has internet access for that. Without a key the app
still starts, but the chatbot cannot answer.

```bash
isoloom generate
OPENAI_API_KEY=sk-... isoloom run docker
```

Then open http://localhost:8501/ and ask for your recent transactions. The same spec runs as
Docker on a local VM (`docker-vm`), on a cloud VM (`cloud-docker`) or on Kubernetes. Lab guide:
WithSecure's [publication](https://labs.withsecure.com/publications/llm-agent-prompt-injection)
on ReAct agent prompt injection and the
[project README](https://github.com/ReversecLabs/damn-vulnerable-llm-agent#readme) (it includes
the solutions).

Upstream version and commit: [UPSTREAM.md](UPSTREAM.md).

## Licence

Apache-2.0, as Damn Vulnerable LLM Agent ([LICENSE](LICENSE)). This application is deliberately
vulnerable: keep it isolated, and use a key with a spending limit.
