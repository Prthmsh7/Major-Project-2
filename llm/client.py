import os
import time
import random
from google import genai
from google.genai import types


def load_local_env() -> None:
    """Populate os.environ from a local .env file when present."""
    for env_file in (".env.local", ".env"):
        if not os.path.exists(env_file):
            continue

        with open(env_file, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'\"")

                if key and key not in os.environ:
                    os.environ[key] = value


class LLMClient:
    """Wrapper for the Gemini LLM API."""
    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash"):
        """
        Initializes the Gemini client.
        If api_key is not provided, it attempts to read GOOGLE_API_KEY or GEMINI_API_KEY.
        """
        load_local_env()
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Set GOOGLE_API_KEY or GEMINI_API_KEY, or add one to .env.local."
            )
            
        self.client = genai.Client(api_key=self.api_key)
        self.model = model
        self.max_retries = 3

    def generate_content(self, prompt: str, system_instruction: str = None) -> str:
        """
        Generates content from the LLM based on the given prompt.
        """
        config = types.GenerateContentConfig(
            temperature=0.2, # Low temperature for more deterministic code generation
        )
        
        if system_instruction:
            config.system_instruction = system_instruction
            
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    config=config
                )
                return response.text
            except Exception as e:
                last_error = e
                message = str(e)

                # Retry transient demand/rate-limit issues.
                transient = (
                    "503" in message
                    or "UNAVAILABLE" in message
                    or "high demand" in message.lower()
                    or "429" in message
                    or "RESOURCE_EXHAUSTED" in message
                    or "Too Many Requests" in message
                )
                if transient and attempt < self.max_retries:
                    delay = min(8.0, (0.75 * (2 ** attempt)) + (random.random() * 0.25))
                    time.sleep(delay)
                    continue

                if "API key not valid" in message or "API_KEY_INVALID" in message:
                    print(
                        "Error communicating with LLM: the API key was rejected. "
                        "Check that .env.local or your shell exports a valid GOOGLE_API_KEY or GEMINI_API_KEY."
                    )
                else:
                    print(f"Error communicating with LLM: {e}")
                break

        return ""
