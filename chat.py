import json
import os
from openai import OpenAI
from dotenv import load_dotenv
import subprocess

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# Initialize OpenAI client
client = OpenAI(
    api_key=api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

def get_system_info(*args, **kwargs):
    try:
        # For posix systems like Linux and MacOS, os.uname() is available.
        system_info = os.uname().sysname if hasattr(os, 'uname') else os.name
        if system_info == "posix":
            if os.path.exists("/System/Library"):
                return "MacOS"
            else:
                return "Linux"
        elif system_info == "nt":
            return "Windows"
        else:
            return "Unknown"
    except Exception as e:
        return str(e)

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        output = result.stdout.strip() if result.stdout else result.stderr.strip()
        return f"✅ Command executed:\n{output}"
    except Exception as e:
        return f"❌ Error: {str(e)}"
    
def write_file(path, content):
    print(f"📝 Writing to {path}")
    
    # ✅ Ensure the directory exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return f"{path} created and code written successfully."


def read_file(file_path):
    if not os.path.exists(file_path):
        return "❌ File not found"
    with open(file_path, 'r') as f:
        return f.read()
    

def fix_errors(error_log: str) -> str:
    """
    A simple heuristic-based error fixer.
    It inspects the error log and returns suggested fixes.
    You can expand these patterns to better fit your needs.
    """
    suggestions = []
    
    if "ModuleNotFoundError" in error_log:
        suggestions.append("It seems a module is missing. Try installing the required package using pip or npm.")
    if "SyntaxError" in error_log:
        suggestions.append("There's a syntax error in your code. Check for missing colons, brackets, or typos.")
    if "Cannot find module" in error_log:
        suggestions.append("A module cannot be found. Ensure that all dependencies are installed and paths are correct.")
    if "port is already in use" in error_log:
        suggestions.append("The port is occupied. Try stopping the process using that port or change the port number.")
    if not suggestions:
        suggestions.append("No specific error fix found. Please review the error log manually.")

    return "\n".join(suggestions)

available_tools = {
    "run_command": {
        "fn": run_command,
        "description": "Executes one or more shell commands and returns the output."
    },
    "read_file": {
        "fn": read_file,
        "description": "Reads and returns the content of a specified file."
    },
    "write_file": {
        "fn": write_file,
        "description": "Writes or overwrites content into a specified file path.",
        "input": {
            "path": "The path to the file that will be written or overwritten.",
            "content": "The text content to be written into the file."
        }
    }, 
    "fix_errors": {
        "fn": fix_errors,
        "description": "Analyzes error logs or stack traces and suggests possible fixes."
    },
    "get_system_info": {
        "fn": get_system_info,
        "description": "Returns the operating system type (Windows, MacOS, Linux, or Unknown)."
    }
}

system_prompt = f"""
    You are a highly skilled AI Coding Agent operating exclusively via the terminal.
    You act like a mini-version of Cursor, assisting users in building and evolving real-world applications directly through the terminal.
    You function using a structured process: start → plan → action → observe.
    You specialize in full-stack development (MERN, FastAPI, JavaScript, Python, etc.) and operate fully via command-line interaction — no GUI.

    You understand existing project context, generate or modify code, fix errors, install dependencies, and run commands.
    

    For the given user query and available tools, plan the step by step execution, based on the planning,
    You operate using available tools (listed below) and can run shell commands, modify files, read project structure, and debug issues — just like a powerful coding terminal agent.
    You are intelligent, cautious, and goal-oriented.
    Wait for the observation and based on the observation from the tool call resolve the user query.

    

    Rules:
    - Always follow the Output JSON Format.
    - Always respond with a single JSON object like: 
        '{{ "step": "plan", "content": "..." }} or '
        '{{ "step": "action", "function": "tool_name", "input": {{ "..." }} }} or '
        '{{ "step": "output", "content": "..." }}. '
        "Never return multiple JSON objects. Do not explain. "
        "Only return one JSON object per message."
    - Always make a new folder with a project name according to the given task and start making files and coding in the folder you made.
    - Operate in one step at a time: start, plan, action, observe, or output.
    - Skip unnecessary steps smartly (e.g., avoid redundant installs).
    - Always cd into the required directory before running commands.
    - Always wait for the observation after `action` before continuing.
    - Auto-confirm prompts: enter y or password Coder_agent@2025 when asked.
    - Detect and handle background processes like npm run dev, vite, etc.
    - Never run dangerous commands (e.g., rm -rf /, disk wipes).
    - Act like a developer-first AI — use clean code, best practices, and proper error handling.
    - Detect, explain, and fix common errors or stack traces automatically.
    - Handle file edits: read, write, append, or refactor code if needed.
    - Perform basic code intelligence: generate components, modify logic, or create files/folders as required.
    - Prioritize developer productivity — fast iterations, automation, and feedback-driven fixes.

    Output JSON Format:
    {{
        "step": "string",
        "content": "string",
        "function": "The name of function if the step is action",
        "input": "The input parameter for the function",
        
    }}

    Available Tools:
    - run_command: Executes one or more shell commands and returns the output.
    - read_file: Reads and returns the content of a specified file.
    - write_file: Writes or overwrites content into a specified file path.
    - fix_errors: Analyzes error logs or stack traces and suggests possible fixes.
    - get_system_info: Returns the operating system type (Windows, MacOS, Linux, or Unknown


    Example 1:
    User Query: "Create a Vite + React TypeScript app and run it"
    Output: {{ "step": "start", "content": "User wants a Vite + React TypeScript project setup. Let's plan the required steps." }}
    Output: {{ "step": "plan", "content": "Plan:\n1. Get system info to check Node availability\n2. Install Vite + React with TypeScript\n3. Start dev server\n4. Return URL"}}
    Output: {{ "step": "action", "function": "get_system_info", "input": ""}}
    Output: {{ "step": "observe", "content": "System: Linux. Proceeding to create the project." }}
    Output: {{ "step": "action", "function": "run_command", "input": "mkdir my-app" }}
    Output: {{ "step": "action", "function": "run_command", "input": "cd my-app" }}
    Output: {{ "step": "action", "function": "run_command", "input": "npm create vite@latest . -- --template react" }}
    Output: {{ "step": "observe", "content": "Vite project created. Next: install dependencies."}}
    Output: {{ "step": "action", "function": "run_command", "input": "cd my-app && npm install" }}
    Output: {{
        "step": "action",
        "function": "write_file",
        "input": {{
            "path": "my-app/src/App.tsx",
            "content": "export default function App() {{\n  return <h1>Hello, Vite + React + TypeScript!</h1>;\n}}"
        }}
    }}
    Output: {{ "step": "action", "function": "run_command", "input": "npm run dev"}}
    Output: {{ "step": "output", "content": "Your app is ready and running at  http://localhost:5173. Tell me if you want to make any changes"}}


    Example 2:
    User Query: "Create a basic ToDo app using HTML, CSS, and JS"
    Output: {{ "step": "start", "content": "User wants a basic ToDo app using HTML, CSS, and JS. Let's plan the steps." }}
    Output: {{ "step": "plan", "content": "Plan:\n1. Create project folder\n2. Create HTML, CSS, and JS files\n3. Implement ToDo logic\n4. Serve via local server" }}
    Output: {{ "step": "action", "function": "run_command", "input": "mkdir todo-app" }}
    Output: {{
        "step": "action",
        "function": "write_file",
        "input": {{
            "path": "todo-app/index.html",
            "content": "<!DOCTYPE html>\\n<html lang='en'>\\n<head>\\n<meta charset='UTF-8'>\\n<title>ToDo App</title>\\n<link rel='stylesheet' href='style.css'>\\n</head>\\n<body>\\n<h1>My ToDo List</h1>\\n<input id='taskInput' type='text' placeholder='New task'>\\n<button onclick='addTask()'>Add</button>\\n<ul id='taskList'></ul>\\n<script src='script.js'></script>\\n</body>\\n</html>"
        }}
    }}
    Output: {{
        "step": "action",
        "function": "write_file",
        "input": {{
            "path": "todo-app/style.css",
            "content": "body {{ font-family: sans-serif; padding: 2em; }}\\nul {{ list-style-type: none; padding: 0; }}\\nli {{ padding: 0.5em 0; }}\\n.completed {{ text-decoration: line-through; color: gray; }}"
        }}
    }}
    Output: {{
        "step": "action",
        "function": "write_file",
        "input": {{
            "path": "todo-app/script.js",
            "content": "function addTask() {{\\n  const input = document.getElementById('taskInput');\\n  const taskText = input.value.trim();\\n  if (taskText === '') return;\\n  const li = document.createElement('li');\\n  li.textContent = taskText;\\n  li.onclick = () => li.classList.toggle('completed');\\n  const delBtn = document.createElement('button');\\n  delBtn.textContent = 'Delete';\\n  delBtn.onclick = (e) => {{ e.stopPropagation(); li.remove(); }};\\n  li.appendChild(delBtn);\\n  document.getElementById('taskList').appendChild(li);\\n  input.value = '';\\n}}"
        }}
    }}
    Output: {{ "step": "observe", "content": "All files created. Open index.html in your browser or use Live Server to preview the ToDo app." }}
    Output: {{ "step": "output", "content": "Your app is ready and running at http://localhost:3000. Tell me if you want to make any changes"}}


    Example 3:
    User Query: "Create a simple node and express server that serves a hello world page"
    Output: {{ "step": "start", "content": "User wants a simple Node.js + Express server that serves a 'Hello World' page. Let's break down the steps." }}  
    Output: {{ "step": "plan", "content": "Plan:\n1. Create project folder\n2. Initialize npm\n3. Install Express\n4. Create server file\n5. Run the server" }}  
    Output: {{ "step": "action", "function": "run_command", "input": "mkdir hello-server" }}  
    Output: {{ "step": "action", "function": "run_command", "input": "cd hello-server && npm init -y" }}  
    Output: {{ "step": "action", "function": "run_command", "input": "cd hello-server && npm install express" }}  
    Output: {{ "step": "action", "function": "write_file", "input": {{ "path": "hello-server/index.js", "content": "const express = require('express');\nconst app = express();\nconst port = 3000;\n\napp.get('/', (req, res) => {{\n  res.send('Hello World');\n}});\n\napp.listen(port, () => {{\n  console.log(`Server listening at http://localhost:${{port}}`);\n}});" }} }}  
    Output: {{ "step": "action", "function": "run_command", "input": "cd hello-server && node index.js" }}  
    Output: {{ "step": "output", "content": "Server running at http://localhost:3000. Visit in browser to see 'Hello World'." }}

     
"""
messages = [
    { "role": "system", "content": system_prompt }
]

while True:
    user_query = input('> ')
    messages.append({ "role": "user", "content": user_query })

    while True:
        response = client.chat.completions.create(
            messages=messages,
            response_format={"type": "json_object"},
            stream=False,
            model="gemini-2.0-flash",
        )

        # parsed_output = json.loads(response.choices[0].message.content)
        try:
            
            content = response.choices[0].message.content
            # content = response['choices'][0]['message']['content']
            if content is None:
                print("❌ No content received from the assistant.")
                continue
            parsed_output = json.loads(content)
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            print(f"👉 Full response: {response}")
            continue

        messages.append({ "role": "assistant", "content": json.dumps(parsed_output) })

        if parsed_output.get("step") == "plan" or parsed_output.get("step") == "observe":
            print(f"🧠: {parsed_output.get('content')}")
            continue
        
        if parsed_output.get("step") == "action":
            tool_name = parsed_output.get("function")
            tool_input = parsed_output.get("input")
            if tool_name == "write_file":
                print(f"🧠: running {tool_name} in {tool_input['path']}")
            else:
                print(f"🧠: running {tool_name}: {tool_input}")


            if available_tools.get(tool_name, False) != False:
                # output = available_tools[tool_name].get("fn")
                tool_fn = available_tools[tool_name].get("fn")
                # output = tool_fn(**tool_input)
                # 🔧 Fix: handle both dict and str inputs
                if isinstance(tool_input, dict):
                    output = tool_fn(**tool_input)
                else:
                    output = tool_fn(tool_input)
                print(f"🧠: output {tool_name}: {output}")
                messages.append({ "role": "assistant", "content": json.dumps({ "step": "observe", "content":  output}) })
                continue

        if parsed_output.get("step") == "get_system":
            tool_name = parsed_output.get("function")
            print(f"🧠: tool_name {tool_name}")

            if available_tools.get(tool_name, False) != False:
                output = available_tools[tool_name].get("fn")()
                print(f"🧠: output {output}")
                messages.append({ "role": "assistant", "content": json.dumps({ "step": "observe", "output":  output}) })
                continue
        
        if parsed_output.get("step") == "output":
            print(f"🤖: {parsed_output.get("content")}")
            break

