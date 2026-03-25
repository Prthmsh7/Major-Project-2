import os
from google import genai
from google.genai import types

class LLMClient:
    """Wrapper for the Gemini LLM API."""
    def __init__(self, api_key: str = None, model: str = "gemini-2.5-flash"):
        """
        Initializes the Gemini client.
        If api_key is not provided, it attempts to read GOOGLE_API_KEY from the environment.
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("API Key is required. Set GOOGLE_API_KEY environment variable.")
            
        self.client = genai.Client(api_key=self.api_key)
        self.model = model

    def generate_content(self, prompt: str, system_instruction: str = None) -> str:
        """
        Generates content from the LLM based on the given prompt.
        """
        config = types.GenerateContentConfig(
            temperature=0.2, # Low temperature for more deterministic code generation
        )
        
        if system_instruction:
            config.system_instruction = system_instruction
            
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config
            )
            return response.text
        except Exception as e:
            print(f"Error communicating with LLM: {e}")
            return ""
