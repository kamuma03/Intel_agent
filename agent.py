from langchain_chroma import Chroma
from langchain_openai import ChatOpenAI
from langchain_classic.memory import ConversationSummaryMemory
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
import sqlite3
from datetime import datetime
import os

def get_ollama_llm(model_name: str = "qwen2.5:32b", base_url: str = "http://localhost:11434"):
    """
    Returns a configured ChatOllama instance.

    Args:
        model_name (str): The name of the Ollama model to use.
        base_url (str): The base URL where Ollama is running.

    Returns:
        ChatOllama: Configured LLM instance.
    """
    return ChatOllama(
        model=model_name,
        base_url=base_url,
        temperature=0.7
    )

class CustomerIntelligenceAgent:
    """
    An agent that maintains a dual-layer memory system:
    1. Short-term Memory: Conversation history (via LangChain's ConversationSummaryMemory).
    2. Long-term Memory: 
       - Vector Store (Chroma) for semantic search of past interactions.
       - Structured Database (SQLite) for specific known facts/preferences.
    
    Supports multiple LLM backends: Ollama (default), OpenAI, Anthropic (Claude), Google (Gemini).
    """

    def __init__(self, user_id, llm_backend="ollama"):
        """
        Initialize the agent with specific user ID and LLM backend.

        Args:
            user_id (str): Unique identifier for the user.
            llm_backend (str): 'ollama', 'openai', 'anthropic', or 'google'. Defaults to 'ollama'.
        """
        self.user_id = user_id
        
        # --- LLM Initialization ---
        if llm_backend == "ollama":
            self.llm = get_ollama_llm()
        elif llm_backend == "openai":
            self.llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
        elif llm_backend == "anthropic" or llm_backend == "claude":
            self.llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.7)
        elif llm_backend == "google" or llm_backend == "gemini":
            self.llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.7)
        else:
            # Default to Ollama if unknown backend
            print(f"Unknown backend '{llm_backend}', defaulting to Ollama.")
            self.llm = get_ollama_llm()
        
        # Using Ollama embeddings for fully local operation
        self.embeddings = OllamaEmbeddings(
            model="nomic-embed-text",
            base_url="http://localhost:11434"
        )

        # --- Short-term Memory (Conversation Context) ---
        # Summarizes conversation to fit within context window while retaining meaning.
        self.short_term_memory = ConversationSummaryMemory(
            llm=self.llm,
            memory_key="chat_history",
            return_messages=True
        )

        # --- Long-term Memory (Semantic Persistence) ---
        # Vector store allows us to find semantically similar past conversations.
        self.vectorstore = Chroma(
            collection_name=f"user_{user_id}_memory",
            embedding_function=self.embeddings,
            persist_directory="./memory_db"
        )

        # --- Structured Memory (Facts/Preferences) ---
        # SQLite database for storing rigid facts (e.g., "likes skiing").
        self.db = sqlite3.connect(f"user_{user_id}.db", check_same_thread=False)
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite preference storage table if it doesn't exist."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT,
                category TEXT,
                timestamp TEXT,
                confidence REAL
            )
        """)
        self.db.commit()

    def save_preference(self, key, value, category, confidence=1.0):
        """
        Store a user preference explicitly in both SQLite and Vector Store.

        Args:
            key (str): The preference key (e.g., "hobby").
            value (str): The preference value (e.g., "chess").
            category (str): Category tag (e.g., "personal").
            confidence (float, optional): Confidence score. Defaults to 1.0.
        """
        # 1. Save to SQLite for exact lookup
        self.db.execute("""
            INSERT OR REPLACE INTO preferences 
            VALUES (?, ?, ?, ?, ?)
        """, (key, value, category, datetime.now().isoformat(), confidence))
        self.db.commit()

        # 2. Save to Vector Store for semantic retrieval
        #    This allows the agent to find this fact even with fuzzy queries.
        self.vectorstore.add_texts(
            texts=[f"{key}: {value}"],
            metadatas=[{"category": category, "type": "preference"}]
        )

    def retrieve_context(self, query):
        """
        Retrieve relevant context from both Vector Store and SQLite.

        Args:
            query (str): The current user message/query.

        Returns:
            str: A formatted string containing relevant past info and preferences.
        """
        # 1. Search vector store for semantically relevant history
        docs = self.vectorstore.similarity_search(query, k=3)
        
        # 2. Get most recent structured preferences
        cursor = self.db.execute("""
            SELECT key, value, category FROM preferences
            ORDER BY timestamp DESC LIMIT 10
        """)
        preferences = cursor.fetchall()
        
        # 3. Format context for the LLM
        context = "Relevant past information:\n"
        if docs:
            context += "\n".join([f"- {doc.page_content}" for doc in docs])
        else:
            context += "(No relevant past context found)"

        context += "\n\nUser preferences:\n"
        if preferences:
            context += "\n".join([f"- {p[0]}: {p[1]} ({p[2]})" for p in preferences])
        else:
            context += "(No known preferences)"
        
        return context

    def respond(self, user_message):
        """
        Generate a personalized response using the full RAG pipeline.

        Args:
            user_message (str): The input message from the user.

        Returns:
            str: The agent's generated response.
        """
        # 1. Retrieve Context (RAG)
        context = self.retrieve_context(user_message)
        
        # 2. Load Short-term History
        chat_history = self.short_term_memory.load_memory_variables({})['chat_history']
        
        # 3. Construct the prompt
        prompt = f"""
        Context about this user (Long-term Memory):
        {context}
        
        Current conversation history (Short-term Memory):
        {chat_history}
        
        User message: {user_message}
        
        Instruction:
        Respond naturally to the user. Use the context provided to personalize your answer.
        If the user asks a question about themselves (e.g., "what do I like?"), refer to the Context.
        """
        
        # 4. Invoke LLM
        response = self.llm.invoke(prompt)
        
        # 5. Update Short-term Memory
        self.short_term_memory.save_context(
            {"input": user_message},
            {"output": response.content}
        )
        
        return response.content
