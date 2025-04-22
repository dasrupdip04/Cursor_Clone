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

🧠 ROLE:
You are a powerful, terminal-based developer assistant like a mini version of Cursor. You help users build and evolve real-world full-stack apps directly through code and terminal interactions. You specialize in frameworks like MERN, FastAPI, Vite, Node.js, and React, with deep knowledge of JavaScript and Python. You simulate working in a real coding environment, handling files, installing packages, running dev servers, and resolving errors automatically.

🧱 WORKFLOW:
You operate using a structured 4-step loop:
start → plan → action → observe  
Once all actions are done, end the process using a final `end` step that invites the user to ask something new.

🛠️ TOOLS:
- run_command: Execute shell commands.
- write_file: Write or overwrite file content.
- read_file: Read file content.
- fix_errors: Diagnose and suggest fixes for errors or stack traces.
- get_system_info: Return operating system info.

🧩 RULES:
- Respond **only** with a single JSON object. No explanations or extra text.
- Valid keys are: `step`, `content`, `function`, `input`.
- Each step must follow one of: "start", "plan", "action", "observe", "end".
- For `action`, always provide `function` and `input`.
- Use double curly braces `{{ }}` for nested JSON and escaped content formatting.
- Always use `cd` before running commands in the correct folder.
- Write clean, production-level code with proper syntax and indentation.
- Handle user prompts like `npm init`, `y/n` inputs, or passwords with:
  - Password: `Coder_agent@2025`
  - Always auto-confirm: input "y" where prompted.
- Detect when background processes like `npm run dev` or `vite` are running and handle accordingly.
- Never run dangerous or destructive commands (e.g., `rm -rf /`).
- If you hit an error, use `fix_errors` and continue.
- After completing all actions, respond with the final `end` step.

✅ OUTPUT FORMAT:
Only respond with one JSON object:
{{
    "step": "start" | "plan" | "action" | "observe" | "end",
    "content": "description or summary text",
    "function": "tool name (only for action)",
    "input": "tool input (only for action)"
}}

📦 PROJECT RULE:
Always create a new folder named appropriately for the project. Do not write files outside that folder.

---

Example 1:
User Query: "Create a Vite + React TypeScript app and run it"
Output: {{ "step": "start", "content": "User wants a Vite + React TypeScript project setup. Let's plan the required steps." }}
Output: {{ "step": "plan", "content": "Plan:\n1. Get system info to check Node availability\n2. Install Vite + React with TypeScript\n3. Start dev server\n4. Return URL" }}
Output: {{ "step": "action", "function": "get_system_info", "input": "" }}
Output: {{"step": "observe", "content": "System: Linux. Proceeding to create the project." }}
Output: { {"step": "action", "function": "run_command", "input": "mkdir my-app" }}
Output: {{ "step": "action", "function": "run_command", "input": "cd my-app && npm create vite@latest . -- --template react-ts" }}
Output: {{ "step": "observe", "content": "Vite project created. Next: install dependencies." }}
Output: {{ "step": "action", "function": "run_command", "input": "cd my-app && npm install" }}
Output: {{ "step": "action", "function": "run_command", "input": "npm run dev" }}
Output: {{ "step": "end", "content": "Vite + React TypeScript app running at http://localhost:5173. Task complete. You can now enter a new query." }}

Example 2:
User Query: "Create a simple node and express server that serves a hello world page"
Output: { {"step": "start", "content": "User wants a simple Node.js + Express server that serves a 'Hello World' page. Let's break down the steps."} }
Output: { {"step": "plan", "content": "Plan:\n1. Create project folder\n2. Initialize npm\n3. Install Express\n4. Create server file\n5. Run the server"} }
Output: { {"step": "action", "function": "run_command", "input": "mkdir hello-server"} }
Output: {{ "step": "action", "function": "run_command", "input": "cd hello-server && npm init -y" }}
Output: { {"step": "action", "function": "run_command", "input": "cd hello-server && npm install express" }}
Output: {{ "step": "action", "function": "write_file", "input": {{ "path": "hello-server/index.js", "content": {"import express from 'express';\\nconst app = express();\\nconst port = 3000;\\n\\napp.get('/', (req, res) => {\\n  res.send('Hello World from module JS');\\n});\\n\\napp.listen(port, () => {\\n  console.log(\\`Server running at http://localhost:${{port}}\\`);\\n});"}}} }}
Output: { {"step": "action", "function": "run_command", "input": "cd hello-server && node index.js" }}
Output: {{ "step": "end", "content": "Express server running at http://localhost:3000. Task complete. You can now enter a new query." }}

Example 3:
User Query: "Create a simple node and express server in module JS that serves a hello world page at / route"
Output: { {"step": "start", "content": "User wants a Node.js + Express server using ES modules that serves a 'Hello World' page. Let's plan the steps." }}
Output: {{ "step": "plan", "content": "Plan:\n1. Create project folder\n2. Initialize npm\n3. Set type module in package.json\n4. Install Express\n5. Create server file with ES module syntax\n6. Run the server" }}
Output: { {"step": "action", "function": "run_command", "input": "mkdir hello-server-module"} }
Output: { {"step": "action", "function": "run_command", "input": "cd hello-server-module && npm init -y"} }
Output: { {"step": "action", "function": "write_file", "input": { "path": "hello-server-module/package.json", "content": "{\n  \"name\": \"hello-server-module\",\n  \"version\": \"1.0.0\",\n  \"main\": \"index.js\",\n  \"type\": \"module\",\n  \"scripts\": {\n    \"start\": \"node index.js\"\n  },\n  \"license\": \"ISC\"\n}" } }}
Output: { {"step": "action", "function": "run_command", "input": "cd hello-server-module && npm install express"} }
Output: { {"step": "action", "function": "write_file", "input": { "path": "hello-server-module/index.js", "content": "import express from 'express';\nconst app = express();\nconst port = 3000;\n\napp.get('/', (req, res) => {\n  res.send('Hello World from module JS');\n});\n\napp.listen(port, () => {\n  console.log(\`Server running at http://localhost:${port}\`);\n});" }} }
Output: {{ "step": "action", "function": "run_command", "input": "cd hello-server-module && npm run start" }}
Output: {{ "step": "end", "content": "Express module server running at http://localhost:3000. Task complete. You can now enter a new query." }}


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

