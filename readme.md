# Self-Correcting Coding Agent (Project 4)

An AI agent that writes and executes Python code, reads its own errors, and fixes them — looping until the code succeeds. Demonstrates the ReAct pattern (reason → act → observe → repeat), the core loop behind most real-world coding and automation agents.

## What it does

Given a coding task, the agent:
1. Writes Python code to accomplish the task
2. Executes it via a tool that runs the script and captures output or errors
3. If it errors, reads the error message and decides how to fix it
4. Re-runs the corrected code
5. Repeats until the code succeeds, or returns to the user with a question if the next step requires a decision it shouldn't make
   on its own (e.g. altering state, like creating a database table)

## Tool

- **run_python_code** — writes the given code to a temp file, executes it, and returns stdout on success or stderr on failure

⚠️ **Note:** this executes model-generated code directly with no sandboxing. Fine for local experimentation with a trusted model; not
safe for production without isolating execution (containers, restricted permissions, timeouts already included here).

## Setup

\`\`\`bash
pip install -r requirements.txt
\`\`\`

Create a `.env` file in the project root:
\`\`\`
ANTHROPIC_API_KEY=your-key-here
\`\`\`

## Run

\`\`\`bash
python agent.py
\`\`\`

Example task that reliably triggers a real fail-fix-succeed cycle: *"Write and run Python code that connects to inventory.db, creates a
products table if it doesn't exist, inserts some sample rows, then queries it. If you hit an error, fix it and run again."*

## What's new vs. Projects 1–3

- **The ReAct loop** — reason about the task, act (run code), observe the result, and repeat, entirely driven by what comes back from the tool rather than any hardcoded retry logic
- **Genuine failure and recovery** — unlike earlier projects where tool calls mostly succeeded, this project is built around the agent seeing real errors and adapting
- **Escalation behavior** — the agent doesn't always retry automatically; when a fix requires a judgment call (e.g. modifying
  state), it may stop and ask instead of assuming permission. A precise system prompt controls how much autonomy it takes.

## Why this project

Project 4 of a series exploring agent-building from first principles, progressing from a single-tool agent to multi-tool, memory,
self-correction, MCP integration, frameworks, and multi-agent systems.