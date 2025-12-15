import os
import sys
from dotenv import load_dotenv
from db_manager import PostgresManager
from memory import PostgresMemoryDB
from agent import SmartAssistant
from llm_providers import OpenAIProvider, ClaudeProvider, GeminiProvider, MockProvider

# Load environment variables from .env file
load_dotenv()

def get_provider():
    """
    Selects the LLM provider based on the LLM_PROVIDER environment variable.
    
    Returns:
        LLMProvider: An instance of the selected provider class.
    """
    provider_name = os.getenv("LLM_PROVIDER", "mock").lower()
    
    if provider_name == "openai":
        return OpenAIProvider()
    elif provider_name == "anthropic" or provider_name == "claude":
        return ClaudeProvider()
    elif provider_name == "gemini" or provider_name == "google":
        return GeminiProvider()
    else:
        print(f"Unknown or missing provider '{provider_name}'. Using MockProvider.")
        return MockProvider()

def main():
    """
    Main Entry Point.
    
    1. Orchestrates the startup of the database container.
    2. Initializes the memory connection.
    3. Sets up the AI Agent with the chosen provider.
    4. Runs an interactive CLI loop for the user.
    """
    print("=== Memory-Driven Customer Intelligence Agent ===")
    
    # 1. Start Database Infrastructure
    # Using Docker to ensure dependencies are met without manual user setup
    print("Initializing Database Infrastructure...")
    db_manager = PostgresManager()
    try:
        # Start container and get internal URL for connection
        full_db_url = db_manager.start_container()
        print(f"Database running at: {db_manager.get_safe_db_url()}")
    except Exception as e:
        print(f"Failed to start database: {e}")
        print("Please ensure Docker is running.")
        sys.exit(1)

    # 2. Connect to MemoryLayer
    print("Connecting to Memory Layer...")
    try:
        # Pass the full URL (with password) to the code that needs it
        memory = PostgresMemoryDB(full_db_url)
    except Exception as e:
        print(f"Failed to connect to memory: {e}")
        sys.exit(1)

    # 3. Setup Agent
    provider = get_provider()
    assistant = SmartAssistant(provider=provider, memory=memory)

    # 4. Interaction Loop
    user_id = "user_123" # Simulating a single user for this demo
    print(f"\nAgent Ready! (User ID: {user_id})")
    print("Type 'exit' to quit. Type 'save <key> <value>' to save a fact manually.")
    
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            
            # Input Validation to prevent DoS/Flooding
            if len(user_input) > 2000:
                print("Error: Input too long (max 2000 chars).")
                continue

            # Handle exit command
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            
            # Handle manual memory save command
            if user_input.lower().startswith("save "):
                # Format: save <key> <value>
                # Split only on first two spaces to allow values with spaces
                parts = user_input.split(" ", 2)
                if len(parts) == 3:
                    key, value = parts[1], parts[2]
                    assistant.save_memory(user_id, key, value)
                    continue
                else:
                    print("Usage: save <key> <value>")
                    continue

            # Process normal chat message
            reply = assistant.respond(user_id, user_input)
            print(f"Agent: {reply}")
            
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
