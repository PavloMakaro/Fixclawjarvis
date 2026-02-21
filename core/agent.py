import json
import re
import traceback
import asyncio
import os
from core.llm import LLMService

class Agent:
    def __init__(self, tools_registry, system_prompt=None):
        self.llm = LLMService()
        self.tools = tools_registry

        # Load system prompt from file if not provided
        if not system_prompt:
            try:
                # Look in root directory now
                with open("system_prompt.txt", "r", encoding="utf-8") as f:
                    self.system_prompt = f.read()
            except Exception as e:
                print(f"Error loading system prompt: {e}")
                self.system_prompt = "You are a helpful AI agent."
        else:
            self.system_prompt = system_prompt

    def _build_prompt(self, history, plan_mode=False):
        # With Native Function Calling, we don't need to inject descriptions into text
        # But we must ensure the placeholder is handled if it exists
        try:
            system_msg = self.system_prompt.format(tool_descriptions="Tools are provided via API.")
        except Exception as e:
            # Fallback if formatting fails (e.g. braces issues)
            try:
                system_msg = self.system_prompt.replace("{tool_descriptions}", "Tools are provided via API.")
            except:
                system_msg = self.system_prompt

        # Inject Plan Mode instructions
        if plan_mode:
            system_msg += "\n\nIMPORTANT: You are in PLAN MODE.\n"
            system_msg += "1. If the user request is complex, first output a plan in <plan>...</plan> tags.\n"
            system_msg += "2. Before every tool call or answer, you MUST use <think>...</think> tags to explain your reasoning step-by-step.\n"
            system_msg += "3. The user wants to see your internal monologue. Be verbose in your <think> blocks."

        messages = [{"role": "system", "content": system_msg}]
        messages.extend(history)
        return messages

    async def run(self, user_input, history=None, tool_context=None, plan_mode=True):
        """
        Main ReAct loop. Yields status updates asynchronously.
        Returns final response text.
        """
        if history is None:
            history = []

        # Add user input to history if it's new
        if not history or history[-1]["role"] != "user":
            history.append({"role": "user", "content": user_input})

        max_turns = 100 # Increased safety limit (effectively "no limit" but safe)
        turn = 0

        definitions = self.tools.get_definitions()

        # State for thinking block detection across chunks
        in_thinking_block = False

        while turn < max_turns:
            turn += 1
            yield {"status": "thinking", "message": "Thinking..."}

            # 1. Call LLM with streaming
            messages = self._build_prompt(history, plan_mode=plan_mode)

            # Use DeepSeek for complex reasoning
            stream_gen = await self.llm.generate(
                messages,
                provider="deepseek",
                model="default",
                stream=True,
                tools=definitions
            )

            response_content = ""
            tool_calls_buffer = [] # List of dicts to reconstruct tool calls

            # Temporary buffer for tag detection
            content_buffer = ""

            try:
                async for chunk in stream_gen:
                    delta = None
                    if hasattr(chunk, 'choices') and chunk.choices:
                         delta = chunk.choices[0].delta

                    if delta:
                        # Handle DeepSeek R1 Reasoning Content (if provided by API)
                        if hasattr(delta, 'reasoning_content') and delta.reasoning_content:
                             yield {"status": "thinking", "content": delta.reasoning_content}

                        # Handle content
                        if delta.content:
                            content_piece = delta.content
                            response_content += content_piece

                            # Simple logic to toggle "thinking" status based on tags
                            # This is a bit heuristic but works for streaming
                            if "<think>" in content_piece:
                                in_thinking_block = True
                                # Split and yield parts
                                parts = content_piece.split("<think>")
                                if parts[0]: yield {"status": "final_stream", "content": parts[0]}
                                # We don't yield the tag itself usually, but for debug we can.
                                # Let's yield the content after tag as thinking
                                if len(parts) > 1:
                                     yield {"status": "thinking", "content": parts[1]}
                                continue

                            if "</think>" in content_piece:
                                in_thinking_block = False
                                parts = content_piece.split("</think>")
                                if parts[0]: yield {"status": "thinking", "content": parts[0]}
                                if len(parts) > 1:
                                     yield {"status": "final_stream", "content": parts[1]}
                                continue

                            if in_thinking_block:
                                yield {"status": "thinking", "content": content_piece}
                            else:
                                yield {"status": "final_stream", "content": content_piece}

                        # Handle tool calls
                        if delta.tool_calls:
                            for tc in delta.tool_calls:
                                if tc.index is not None:
                                    while len(tool_calls_buffer) <= tc.index:
                                        tool_calls_buffer.append({"id": "", "function": {"name": "", "arguments": ""}, "type": "function"})

                                    current_tc = tool_calls_buffer[tc.index]
                                    if tc.id:
                                        current_tc["id"] += tc.id
                                    if tc.function:
                                        if tc.function.name:
                                            current_tc["function"]["name"] += tc.function.name
                                        if tc.function.arguments:
                                            current_tc["function"]["arguments"] += tc.function.arguments

            except asyncio.CancelledError:
                raise  # Propagate cancellation immediately
            except Exception as e:
                print(f"Error in stream: {e}")
                pass

            # Prepare Assistant Message
            assistant_msg = {"role": "assistant", "content": response_content}
            if tool_calls_buffer:
                assistant_msg["tool_calls"] = tool_calls_buffer

            history.append(assistant_msg)

            # 2. Check for Tool Call
            if tool_calls_buffer:
                tasks = []
                calls_metadata = []

                for tool_call in tool_calls_buffer:
                    func_name = tool_call["function"]["name"]
                    args_str = tool_call["function"]["arguments"]
                    call_id = tool_call["id"]

                    try:
                        args = json.loads(args_str)
                    except:
                        args = {} # Or handle error

                    yield {"status": "tool_use", "tool": func_name, "args": args}
                    calls_metadata.append({"id": call_id, "name": func_name})

                    # Prepare execution wrapper
                    async def execute_tool_safe(name, arguments):
                        try:
                            if self.tools.is_async(name):
                                res = self.tools.execute(name, tool_context=tool_context, **arguments)
                                if asyncio.iscoroutine(res):
                                    return await res
                                return res
                            else:
                                return await asyncio.to_thread(self.tools.execute, name, tool_context=tool_context, **arguments)
                        except Exception as e:
                            return f"Error executing tool '{name}': {str(e)}"

                    tasks.append(execute_tool_safe(func_name, args))

                # Parallel Execution
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process Results
                for i, result in enumerate(results):
                    meta = calls_metadata[i]
                    func_name = meta["name"]
                    call_id = meta["id"]

                    if isinstance(result, Exception):
                        result_str = f"Error: {str(result)}"
                    else:
                        result_str = str(result)

                    # CROP RESULT (Observation)
                    # Increased limit for clearer debugging if needed, but 2000 is usually fine
                    if len(result_str) > 4000:
                        result_str = result_str[:4000] + "... (truncated)"

                    # Append Tool Message (OpenAI format)
                    history.append({
                        "role": "tool",
                        "tool_call_id": call_id,
                        "content": result_str,
                        "name": func_name
                    })

                    result_msg = f"Tool '{func_name}' output:\n{result_str}"
                    yield {"status": "observation", "result": result_msg}

            else:
                # No tool call = Final Answer
                yield {"status": "final", "content": response_content}
                return

        yield {"status": "final", "content": "Error: Maximum turns reached (100)."}
