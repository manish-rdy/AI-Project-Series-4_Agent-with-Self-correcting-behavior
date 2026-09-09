# Self-Correcting Coding Agent

This project supports both Anthropic and OpenAI API keys. The agent writes Python code, runs it, reads its own errors, and keeps fixing until the script succeeds.

## What it does

Given a coding task, the agent:
1. Writes Python code to accomplish the task
2. Executes it via a tool that runs the script and captures output or errors
3. If it errors, reads the error message and decides how to fix it
4. Re-runs the corrected code
5. Repeats until the code succeeds, or stops when it needs a human decision

## Tool

- **run_python_code** — writes the provided code to a temporary script, executes it, and returns stdout on success or stderr on failure

⚠️ **Note:** this executes model-generated code directly with no sandboxing. Fine for local experimentation with a trusted model; not safe for production without isolating execution in a container or restricted environment.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root. You can use either provider:

```bash
# choose one provider
LLM_PROVIDER=openai

# OpenAI settings
OPENAI_API_KEY=your_openai_key_here
OPENAI_MODEL=gpt-4o-mini

# Anthropic settings
ANTHROPIC_API_KEY=your_anthropic_key_here
ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

If you only have one API key configured, the app will auto-select it. If both are present, set `LLM_PROVIDER` explicitly.

## Run

```bash
python agent.py --provider openai
```

or

```bash
python agent.py --provider anthropic
```

If you omit the flag, the app will infer the provider from the environment.

## Example task

> "Write and run Python code that connects to `inventory.db`, creates a `products` table if it doesn't exist, inserts sample rows, and queries it. If you hit an error, fix it and run again."

## Why this project

This version keeps the same self-correcting ReAct loop while supporting either Anthropic or OpenAI credentials and models.