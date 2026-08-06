import os
import anthropic 
from dotenv import load_dotenv
import subprocess

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def run_python_code(code):
    with open("temp_script.py","w") as f:
        f.write(code)

    result = subprocess.run(
        ["py","temp_script.py"],
        capture_output=True,
        text=True,
        timeout=10
    )    

    if result.returncode == 0:
        return f"Success. output:\n{result.stdout}"
    else:
        return f"Error:\n{result.stderr}"

tools = [
    {
        "name": "run_python_code",
        "description": "Write and execute a python script.Returns the output if it ran successfully or the error message if it fails.",
        "input_schema": {
            "type": "object",
            "properties": {"code": {"type":"string", "description":"The full python code to execute."}},
            "required": ["code"]
        }
    }
]

def run_agent(user_message):
    messages = [{"role":"user", "content":user_message}]
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system="You are a coding agent. When you erite code, run it using run_python_code tool. If it errors, read the error carefully, fix the code and run it again."
            "Keep trying until it succeeds or you're confident it's not fixable.",
            tools=tools,
            messages=messages
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason!= "tool_use":
            for block in response.content:
                if block.type=="text":
                    print(block.text)
            return

        tool_results = []

        for block in response.content:
            if block.type == "tool_use":
                if block.name == "run_python_code":
                    result = run_python_code(**block.input)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result)
                })     

        messages.append({"role": "user", "content": tool_results})


if __name__=="__main__":
    #run_agent("Write and run Python code that connects to a SQLite database file called 'inventory.db' and queries a table called 'products'. Just try it directly — don't add error handling preemptively.")
    run_agent("Yes, proceed with option B.")