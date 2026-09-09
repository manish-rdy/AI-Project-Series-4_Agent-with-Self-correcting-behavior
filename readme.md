# Self-Correcting Coding Agent (OpenAI version)

This is a replica of the Anthropic-based self-correcting coding agent, reworked to use OpenAI API keys and the OpenAI chat-completions API instead.

## What it does

Given a coding task, the agent:
1. Writes Python code to accomplish the task
2. Executes it via a tool that runs the script and captures output or errors
3. If it errors, reads the error message and decides how to fix it
4. Re-runs the corrected code
5. Repeats until the code succeeds, or returns to the user with a question if the next step requires a decision it shouldn't make on its own

## Tool

- **run_python_code** — writes the provided code to a temporary script, executes it, and returns stdout on success or stderr on failure

⚠️ **Note:** this executes model-generated code directly with no sandboxing. Fine for local experimentation with a trusted model; not safe for production without isolating execution in a container or restricted environment.

## Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file in the project root:

```bash
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4o-mini
```

You can swap `gpt-4o-mini` for any model supported by your OpenAI account, such as `gpt-4o` or `gpt-4.1-mini`.

## Run

```bash
python agent.py
```

Example task that triggers a real fail-fix-succeed cycle:

> "Write and run Python code that connects to `inventory.db`, creates a `products` table if it doesn't exist, inserts sample rows, and queries it. If you hit an error, fix it and run again."

## Why this project

This version keeps the same self-correcting ReAct loop while using OpenAI credentials and model access instead of Anthropic.