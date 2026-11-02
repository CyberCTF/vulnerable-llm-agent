#!/bin/sh
# Starts the agent, on OpenAI when a key is given, else on the local stand-in model (backend.sh).
set -e
. /opt/standin/backend.sh
if [ "$STANDIN" = 1 ]; then
  python /opt/standin/server.py 8000 &
fi
exec streamlit run main.py --server.port=8501 --server.address=0.0.0.0
