import os
from openai import AsyncOpenAI
from typing import AsyncGenerator, Union, List, Dict, Any
import config

class LLMService:
    def __init__(self):
        # Initialize Groq client
        self.groq_client = AsyncOpenAI(
            api_key=config.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )

        # Initialize DeepSeek client
        self.deepseek_client = AsyncOpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com"
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama3-70b-8192", # Groq model default
        provider: str = "groq",
        temperature: float = 0.7,
        stream: bool = False,
        tools: List[Dict[str, Any]] = None,
    ) -> Union[Any, AsyncGenerator[Any, None]]:
        """
        Generates response via Groq or DeepSeek API.
        Returns message object (non-stream) or async generator of chunks (stream).

        DeepSeek Caching:
        DeepSeek automatically caches prompts that share the same prefix (system prompt + history).
        Ensure the system prompt is static and identical across requests to maximize caching hits.
        """
        try:
            client = self.groq_client
            if provider == "deepseek":
                client = self.deepseek_client
                if model == "default":
                    model = "deepseek-chat"
                # Note: deepseek-reasoner (R1) does not support tools yet (as of Feb 2025).
                # Use deepseek-chat (V3) for tool-use agents.

            tool_choice = "auto" if tools and "reasoner" not in model else None

            if stream:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    stream=True,
                    tools=tools if tool_choice else None,
                    tool_choice=tool_choice
                )

                # Wrap generator to yield raw chunks
                async def stream_generator() -> AsyncGenerator[Any, None]:
                    async for chunk in response:
                        yield chunk

                return stream_generator()

            else:
                response = await client.chat.completions.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    stream=False,
                    tools=tools if tool_choice else None,
                    tool_choice=tool_choice
                )
                return response.choices[0].message

        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            if stream:
                async def error_gen() -> AsyncGenerator[str, None]:
                    yield error_msg
                return error_gen()
            return error_msg
