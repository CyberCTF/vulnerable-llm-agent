# Upstream's Dockerfile (app/Dockerfile) with four changes:
# - the base image is pinned to python:3.9.25-slim-bookworm (upstream: python:3.9-slim, whose
#   newer Debian no longer has software-properties-common);
# - requirements.txt leaves most versions open (no lockfile), so pip is upgraded to a release
#   that knows --uploaded-prior-to and resolves every dependency as of upstream's last commit
#   (2025-06-25), which keeps the build reproducible;
# - model_name, which upstream's .env.openai.template sets, is baked in (openai-gpt-4o); the
#   OpenAI key itself is not: the runner passes OPENAI_API_KEY at launch (an Isoloom input);
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

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
