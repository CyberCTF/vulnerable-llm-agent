# Upstream

| | |
| --- | --- |
| Project | Damn Vulnerable LLM Agent |
| Repository | https://github.com/ReversecLabs/damn-vulnerable-llm-agent (formerly WithSecureLabs) |
| Version | main (no releases; last commit 2025-06-25) |
| Commit | c0cf9a14adad76e9d6a53c41741f625334bd9971 |
| Licence | Apache-2.0 |

`build/agent/app/` is that commit, unchanged, without its Git history. `build/agent/Dockerfile`
is upstream's Dockerfile with the base image pinned to `python:3.9.25-slim-bookworm`, pip
upgraded and `PIP_UPLOADED_PRIOR_TO` set to the commit's date (upstream's requirements are mostly
unpinned), `model_name=openai-gpt-4o` baked in (the value of upstream's `.env.openai.template`),
and the source copied from `app/`. The OpenAI key is never baked in: Isoloom passes
`OPENAI_API_KEY` at launch. To update, replace `build/agent/app/` with a newer commit, then
change this table and the date.
