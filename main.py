import os
import sys
from dotenv import load_dotenv
from agent import CustomerIntelligenceAgent

# Load environment variables from .env file
load_dotenv()

def main():
    """
    Main Entry Point for the Customer Intelligence Agent CLI.
    
    This function:
    1. Initializes the agent with the specified LLM provider (Ollama or OpenAI).
    2. Runs an interactive loop for user chat and command input.
    3. Handles manual preference saving and graceful exit.
    """
    print("=== Memory-Driven Customer Intelligence Agent (LangChain RAG) ===")
    
    # 1. Configuration
    user_id = "user_123" 
    
    # Check for LLM_PROVIDER env var to switch between local execution (Ollama) and cloud (OpenAI)
    # Default is 'ollama' for local privacy and cost-savings.
    llm_provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    print(f"Initializing agent with provider: {llm_provider}")
    
    try:
        agent = CustomerIntelligenceAgent(user_id=user_id, llm_backend=llm_provider)
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        print("Please check your API keys or Ollama connection.")
        sys.exit(1)

    print(f"\nAgent Ready! (User ID: {user_id})")
    print("Type 'exit' to quit. Type 'save <key> <value> <category>' to save a preference manually.")
    
    # 2. Interactive Loop
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            
            # Handle exit command
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            
            # 3. Handle Commands
            # Command: save <key> <value> <category>
            if user_input.lower().startswith("save "):
                parts = user_input.split(" ", 3)
                if len(parts) >= 4:
                    key = parts[1]
                    value = parts[2]
                    category = parts[3]
                    agent.save_preference(key, value, category)
                    print(f"Saved preference: {key}={value} ({category})")
                    continue
                else:
                    print("Usage: save <key> <value> <category>")
                    continue

            # 4. Process Chat Message
            reply = agent.respond(user_input)
            print(f"Agent: {reply}")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
