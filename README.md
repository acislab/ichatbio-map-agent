# ichatbio-agent-example

A template for making new iChatBio agents.

## Quickstart

*Requires python 3.10 or higher*

Set up your development environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

Run the server:

```bash
uvicorn src.agent:create_app --factory --reload
```

You can also run the agent server as a Docker container:

```bash
docker compose up --build
```

If everything worked, you should be able to find your agent card at http://localhost:9999/.well-known/agent.json.
