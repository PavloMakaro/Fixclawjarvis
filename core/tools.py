import os
import glob
import importlib.util
import inspect
import asyncio
import config
import sys
import traceback

class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self.descriptions = []
        self.context = {}
        self.allowed_users = getattr(config, "ALLOWED_USERS", [])

    def set_global_context(self, **kwargs):
        """Set global context variables available to tools."""
        self.context.update(kwargs)

    def register(self, name, func, description, requires_context=False):
        """Register a new tool."""
        is_async = inspect.iscoroutinefunction(func)
        self.tools[name] = {
            "func": func,
            "description": description,
            "requires_context": requires_context,
            "is_async": is_async
        }

        try:
            sig = inspect.signature(func)
            internal_args = ["bot", "chat_id", "context", "job_queue", "registry"]
            params = [p.name for p in sig.parameters.values() if p.name not in internal_args]
            args_desc = ", ".join(params)
        except:
            args_desc = "..."

        self.descriptions.append(f"- {name}({args_desc}): {description}")

    def load_modules(self, modules_dir="modules"):
        """Load python files from modules directory."""
        if not os.path.exists(modules_dir):
            os.makedirs(modules_dir)

        for filepath in glob.glob(os.path.join(modules_dir, "*.py")):
            module_name = os.path.basename(filepath)[:-3]
            if module_name == "__init__":
                continue

            try:
                spec = importlib.util.spec_from_file_location(module_name, filepath)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    if hasattr(module, "register_tools"):
                        module.register_tools(self)
                        print(f"Loaded module: {module_name}")
            except Exception as e:
                print(f"Error loading module {module_name} from {filepath}: {e}")
                traceback.print_exc()

    def reload_modules(self):
        """Reloads all modules dynamically."""
        self.tools = {}
        self.descriptions = []
        # We need to invalidate cache to force re-read from disk
        to_remove = []
        for name, module in sys.modules.items():
            # Rough check if it's one of our dynamic modules
            # They are usually loaded as 'module_name' or similar if not package
            # Since we used spec_from_file_location(module_name), the key in sys.modules might be just the name
            # But let's check `modules_dir` path
            if hasattr(module, "__file__") and module.__file__ and "modules" in module.__file__:
                to_remove.append(name)

        for name in to_remove:
            if name in sys.modules:
                del sys.modules[name]

        print("Reloading modules...")
        self.load_modules()
        return "Modules reloaded."

    def is_async(self, tool_name):
        if tool_name in self.tools:
            return self.tools[tool_name]["is_async"]
        return False

    def execute(self, tool_name, tool_context=None, **kwargs):
        """Execute a tool by name. If async, returns coroutine."""
        if tool_name not in self.tools:
            return f"Error: Tool '{tool_name}' not found."

        # Check authorization if context provided
        if tool_context and "chat_id" in tool_context:
            chat_id = str(tool_context["chat_id"])
            if self.allowed_users:
                 if chat_id not in self.allowed_users:
                     return f"Error: User {chat_id} is not authorized to use tools."

        tool_info = self.tools[tool_name]
        func = tool_info["func"]

        # Merge contexts
        current_context = self.context.copy()
        if tool_context:
            current_context.update(tool_context)

        try:
            if tool_info["requires_context"]:
                # Inject context into kwargs
                for k, v in current_context.items():
                    if k not in kwargs:
                        kwargs[k] = v

            return func(**kwargs)
        except Exception as e:
            return f"Error executing tool '{tool_name}': {str(e)}"

    def get_descriptions(self):
        """Get formatted descriptions of all tools."""
        return "\n".join(self.descriptions)

    def get_definitions(self):
        """Generate OpenAI-compatible tool definitions."""
        definitions = []
        internal_args = ["bot", "chat_id", "context", "job_queue", "registry"]

        for name, info in self.tools.items():
            func = info["func"]
            desc = info["description"]

            # Build parameters schema
            properties = {}
            required = []

            try:
                sig = inspect.signature(func)
                for param_name, param in sig.parameters.items():
                    if param_name in internal_args or param_name in ["kwargs", "args"]:
                        continue

                    # Determine type (default to string)
                    param_type = "string"
                    if param.annotation != inspect.Parameter.empty:
                         if param.annotation == int:
                             param_type = "integer"
                         elif param.annotation == float:
                             param_type = "number"
                         elif param.annotation == bool:
                             param_type = "boolean"
                         elif param.annotation == list:
                             param_type = "array"
                         elif param.annotation == dict:
                             param_type = "object"

                    properties[param_name] = {"type": param_type}

                    # Assume all positional args without default are required
                    if param.default == inspect.Parameter.empty:
                        required.append(param_name)
            except:
                pass

            definitions.append({
                "type": "function",
                "function": {
                    "name": name,
                    "description": desc,
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            })
        return definitions
