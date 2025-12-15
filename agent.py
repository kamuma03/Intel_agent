from memory import PostgresMemoryDB
from llm_providers import LLMProvider

class SmartAssistant:
    """
    The core agent class responsible for coordinating memory and intelligence.
    
    It handles:
    1. Saving user facts.
    2. Logging interactions.
    3. Retrieving context (facts + history).
    4. Generating responses via the attached LLM Provider.
    """
    def __init__(self, provider: LLMProvider, memory: PostgresMemoryDB):
        """
        Initialize the Assistant.
        
        Args:
            provider (LLMProvider): The LLM backend to use (OpenAI, Claude, etc.).
            memory (PostgresMemoryDB): The storage backend for persistence.
        """
        self.provider = provider
        self.memory = memory

    def save_memory(self, user_id, key, value):
        """
        Manually saves a specific fact about the user to the database.
        
        Args:
            user_id (str): The ID of the user.
            key (str): The fact key.
            value (str): The fact value.
        """
        self.memory.save_memory(user_id, key, value)
        print(f"[Memory] Saved {key}={value} for user {user_id}")

    def respond(self, user_id, message):
        """
        Generates a response to a user message using context from memory.
        
        Args:
            user_id (str): The ID of the user.
            message (str): The user's input message.
            
        Returns:
            str: The assistant's response.
        """
        
        # 1. Log User Input
        # We record what the user said *before* generating a response
        self.memory.log_interaction(user_id, "user", message)
        
        # 2. Retrieve Context
        #   a. Recent conversation history (last 5 messages) to maintain flow
        history = self.memory.get_recent_history(user_id, limit=5)
        
        #   b. Explicit memories (facts)
        #   Retrieve keys like 'name', 'preferences', etc.
        facts = self.memory.get_all_memories(user_id)
        
        # Construct context string for the LLM
        # We inject facts into the system/prompt so the LLM "knows" these things.
        fact_str = "\n".join([f"{k}: {v}" for k, v in facts.items()])
        system_context = f"User Profile/Facts:\n{fact_str}\n" if facts else ""
        
        # Prepare context list for provider
        # 'history' contains the chat logs
        full_context = history
        
        # 3. Generate Response
        # We assume the prompt is the system context + the current user message.
        # This approach ensures the LLM sees the latest facts immediately.
        prompt_with_context = f"{system_context}\nUser: {message}"
        
        print(f"[Agent] Generating response for {user_id}...")
        reply = self.provider.generate(prompt_with_context, full_context)
        
        # 4. Log Assistant Response
        # We record what the assistant said so it can be recalled in future history.
        self.memory.log_interaction(user_id, "assistant", reply)
        
        return reply
