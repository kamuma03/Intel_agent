from abc import ABC, abstractmethod
import os
import openai
from anthropic import Anthropic
import google.generativeai as genai

class LLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers.
    
    Ensures that all LLM implementations (OpenAI, Claude, Gemini) 
    adhere to a common interface for easy swapping.
    """
    @abstractmethod
    def generate(self, prompt: str, context: list) -> str:
        """
        Generates a response given a prompt and conversation context.
        
        Args:
            prompt (str): The latest user message or system formatted prompt.
            context (list): A list of previous message dictionaries.
            
        Returns:
            str: The text response from the LLM.
        """
        pass

class OpenAIProvider(LLMProvider):
    """Provider for OpenAI's GPT models."""
    def __init__(self, api_key=None, model="gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key)
        else:
            print("Warning: OPENAI_API_KEY not found.")

    def generate(self, prompt: str, context: list) -> str:
        if not self.api_key:
            return "Error: OpenAI API Key missing."
        
        messages = [{"role": "system", "content": "You are a helpful assistant."}]
        
        # Convert context frames to OpenAI message format
        for msg in context:
            role = "user" if msg['role'] == 'user' else "assistant"
            messages.append({"role": role, "content": msg['content']})
        
        # Add the current prompt
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content

class ClaudeProvider(LLMProvider):
    """Provider for Anthropic's Claude models."""
    def __init__(self, api_key=None, model="claude-3-opus-20240229"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        if self.api_key:
            self.client = Anthropic(api_key=self.api_key)
        else:
            print("Warning: ANTHROPIC_API_KEY not found.")

    def generate(self, prompt: str, context: list) -> str:
        if not self.api_key:
            return "Error: Anthropic API Key missing."

        # Format messages for Claude
        messages = []
        for msg in context:
             messages.append({"role": msg['role'], "content": msg['content']})
        
        messages.append({"role": "user", "content": prompt})

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=messages
        )
        return response.content[0].text

class GeminiProvider(LLMProvider):
    """Provider for Google's Gemini models."""
    def __init__(self, api_key=None, model="gemini-pro"):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model_instance = genai.GenerativeModel(self.model)
        else:
            print("Warning: GOOGLE_API_KEY not found.")

    def generate(self, prompt: str, context: list) -> str:
        if not self.api_key:
            return "Error: Google API Key missing."
        
        # Construct chat history for Gemini's start_chat method
        # Maps standard roles to Gemini roles ('user' -> 'user', 'assistant' -> 'model')
        chat = self.model_instance.start_chat(history=[
            {"role": "user" if msg['role'] == "user" else "model", "parts": [msg['content']]}
            for msg in context
        ])
        
        response = chat.send_message(prompt)
        return response.text

class MockProvider(LLMProvider):
    """
    Fallback provider if no API keys are present.
    Used for testing the infrastructure without incurring costs.
    """
    def generate(self, prompt: str, context: list) -> str:
        return f"[MOCK AI] I received your message: '{prompt}'. Context size: {len(context)}"
