import argparse
import json
import os
import subprocess

from dotenv import load_dotenv

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None

from openai import OpenAI

load_dotenv()

SYSTEM_PROMPT = (
    "You are a coding agent. When you write code, run it using the run_python_code tool. "
    "If it errors, read the error carefully, fix the code, and run it again. "
    "Keep trying until it succeeds or you are confident it is not fixable."
)

openai_tools = [
    {
        "type": "function",
        "function": {
            "name": "run_python_code",
            "description": "Write and execute a Python script. Returns the output if it ran successfully or the error message if it fails.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The full Python code to execute.",
                    }
                },
                "required": ["code"],
            },
        },
    }
]

anthropic_tools = [
    {
        "name": "run_python_code",
        "description": "Write and execute a Python script. Returns the output if it ran successfully or the error message if it fails.",
        "input_schema": {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "The full Python code to execute.",
                }
            },
            "required": ["code"],
        },
    }
]


def resolve_provider(explicit_provider=None):
    provider = (explicit_provider or os.getenv("LLM_PROVIDER", "")).strip().lower()
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if provider:
        if provider not in {"openai", "anthropic"}:
            raise ValueError("LLM_PROVIDER must be either 'openai' or 'anthropic'.")
        if provider == "openai" and not openai_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai.")
        if provider == "anthropic" and not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY is required when LLM_PROVIDER=anthropic.")
        return provider

    if openai_key and not anthropic_key:
        return "openai"
    if anthropic_key and not openai_key:
        return "anthropic"
    if openai_key and anthropic_key:
        raise ValueError(
            "Multiple API keys are configured. Set LLM_PROVIDER to 'openai' or 'anthropic' to choose which one to use."
        )

    raise ValueError(
        "No API key configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY and optionally LLM_PROVIDER."
    )


def build_client(provider):
    if provider == "anthropic":
        if anthropic is None:
            raise ImportError("The 'anthropic' package is not installed. Install it with: pip install anthropic")
        return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def run_python_code(code):
    with open("temp_script.py", "w", encoding="utf-8") as f:
        f.write(code)

    result = subprocess.run(
        ["python", "temp_script.py"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    if result.returncode == 0:
        return f"Success. output:\n{result.stdout}"
    return f"Error:\n{result.stderr}"


def run_openai_agent(user_message, client):
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            max_tokens=1024,
            temperature=0.2,
            tools=openai_tools,
            messages=messages,
        )

        assistant_message = response.choices[0].message
        messages.append(
            {
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": (
                    [
                        {
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments,
                            },
                        }
                        for tool_call in assistant_message.tool_calls or []
                    ]
                    if assistant_message.tool_calls
                    else None
                ),
            }
        )

        if not assistant_message.tool_calls:
            if assistant_message.content:
                print(assistant_message.content)
            return

        for tool_call in assistant_message.tool_calls:
            if tool_call.function.name == "run_python_code":
                arguments = json.loads(tool_call.function.arguments)
                result = run_python_code(**arguments)
            else:
                result = f"Unknown tool: {tool_call.function.name}"

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(result),
                }
            )


def run_anthropic_agent(user_message, client):
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=anthropic_tools,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        tool_uses = [block for block in response.content if block.type == "tool_use"]
        if not tool_uses:
            for block in response.content:
                if block.type == "text":
                    print(block.text)
            return

        tool_results = []
        for block in tool_uses:
            if block.name == "run_python_code":
                result = run_python_code(**block.input)
            else:
                result = f"Unknown tool: {block.name}"

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                }
            )

        messages.append({"role": "user", "content": tool_results})


def run_agent(user_message, provider=None):
    provider = resolve_provider(provider)
    client = build_client(provider)

    if provider == "openai":
        run_openai_agent(user_message, client)
    else:
        run_anthropic_agent(user_message, client)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the self-correcting coding agent with either OpenAI or Anthropic.")
    parser.add_argument(
        "--provider",
        choices=["openai", "anthropic"],
        help="Choose which API provider to use. If omitted, it is inferred from environment variables.",
    )
    args = parser.parse_args()

    run_agent(
        "Write and run Python code that connects to a SQLite database file called 'inventory.db', creates a 'products' table if it doesn't exist, inserts sample rows, and queries it. If you hit an error, fix it and run again.",
        provider=args.provider,
    )
