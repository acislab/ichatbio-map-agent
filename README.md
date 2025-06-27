# ichatbio-agent-example

A template for making new iChatBio agents.

## Quickstart

*Requires python 3.10 or higher*

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start up the agent web server
python src
```

If everything worked, you should be able to find your agent card at http://localhost:9999/.well-known/agent.json.