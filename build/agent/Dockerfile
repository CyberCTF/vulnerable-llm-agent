# Upstream's Dockerfile (app/Dockerfile) with five changes:
# - the base image is pinned to python:3.9.25-slim-bookworm (upstream: python:3.9-slim, whose
#   newer Debian no longer has software-properties-common);
# - requirements.txt leaves most versions open (no lockfile), so pip is upgraded to a release
#   that knows --uploaded-prior-to and resolves every dependency as of upstream's last commit
#   (2025-06-25), which keeps the build reproducible;
# - model_name, which upstream's .env.openai.template sets, is baked in (openai-gpt-4o); no key is;
# - it starts through start.sh, which points the agent at the local stand-in model
#   (standin/server.py) unless an OpenAI key is given (OPENAI_API_KEY), so it needs neither;
# - COPY reads app/.
FROM python:3.9.25-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    pip \
    && rm -rf /var/lib/apt/lists/*

ENV PIP_UPLOADED_PRIOR_TO=2025-06-25T13:58:42Z
ENV model_name=openai-gpt-4o
RUN pip install --no-cache-dir pip==26.0.1

RUN pip install python-dotenv

COPY app/* /app/
RUN pip3 install -r requirements.txt

COPY app/config.toml /root/.streamlit/config.toml

# The transactions database lives in /app/data (a volume) so ctf/flag.sh can put the CTF flag in
# it before the agent seeds the rest; the application opens it at its usual path (a symlink).
RUN mkdir -p /app/data && ln -s /app/data/transactions.db /app/transactions.db

COPY standin/server.py /opt/standin/server.py
COPY backend.sh start.sh /opt/standin/
# The lab's solve check (isoloom.yml), run in the machine; it replays upstream's README solutions.
COPY check/solve.sh /opt/check/solve.sh

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["/opt/standin/start.sh"]
