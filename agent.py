import json
import os
import subprocess

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


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


tools = [
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


def run_agent(user_message):
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            max_tokens=1024,
            temperature=0.2,
            tools=tools,
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


if __name__ == "__main__":
    run_agent(
        "Write and run Python code that connects to a SQLite database file called 'inventory.db', creates a 'products' table if it doesn't exist, inserts sample rows, and queries it. If you hit an error, fix it and run again."
    )
