import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime

class PostgresMemoryDB:
    """
    A permanent memory storage layer using PostgreSQL.
    
    This class handles the creation of schema tables and provides methods
    to save/retrieve structured user facts (memories) and conversation logs.
    """
    def __init__(self, db_url):
        """
        Initialize the DB connection.
        
        Args:
            db_url (str): The connection string for PostgreSQL.
        """
        self.db_url = db_url
        self._init_db()

    def _get_connection(self):
        """Helper to get a fresh database connection using psycopg2."""
        return psycopg2.connect(self.db_url)

    def _init_db(self):
        """
        Initializes the database schema.
        
        Creates the 'memories' and 'interactions' tables if they do not exist.
        This ensures the database structure is always present on startup.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                # Table: memories
                # Stores specific key-value facts about users (e.g., preference: travel=Japan)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS memories (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        key TEXT NOT NULL,
                        value TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, key)
                    );
                """)
                
                # Table: interactions
                # Stores raw chat logs for context retrieval
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS interactions (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    );
                """)
            conn.commit()

    def save_memory(self, user_id, key, value):
        """
        Saves or updates a specific fact about a user.
        
        Uses ON CONFLICT DO UPDATE to ensure keys are unique per user.
        
        Args:
            user_id (str): The ID of the user.
            key (str): The name of the fact (e.g., 'hobby').
            value (str): The value of the fact (e.g., 'skiing').
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO memories (user_id, key, value)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, key) 
                    DO UPDATE SET value = EXCLUDED.value;
                """, (user_id, key, value))
            conn.commit()

    def get_memory(self, user_id, key):
        """
        Retrieves a specific memory fact for a user.
        
        Args:
            user_id (str): The ID of the user.
            key (str): The specific fact key to retrieve.
            
        Returns:
            str or None: The value of the fact, or None if not found.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT value FROM memories 
                    WHERE user_id = %s AND key = %s;
                """, (user_id, key))
                result = cur.fetchone()
                return result[0] if result else None

    def get_all_memories(self, user_id):
        """
        Retrieves all stored facts for a user.
        
        Args:
            user_id (str): The ID of the user.
            
        Returns:
            dict: A dictionary of key-value pairs representing user facts.
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT key, value FROM memories 
                    WHERE user_id = %s;
                """, (user_id,))
                results = cur.fetchall()
                return {row['key']: row['value'] for row in results}

    def log_interaction(self, user_id, role, content):
        """
        Logs a chat interaction (user query or assistant response).
        
        Args:
            user_id (str): The ID of the user.
            role (str): 'user' or 'assistant'.
            content (str): The text message content.
        """
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO interactions (user_id, role, content)
                    VALUES (%s, %s, %s);
                """, (user_id, role, content))
            conn.commit()

    def get_recent_history(self, user_id, limit=5):
        """
        Retrieves the most recent interactions for context.
        
        Args:
            user_id (str): The ID of the user.
            limit (int): Number of recent messages to retrieve.
            
        Returns:
            list: A list of dicts [{'role':..., 'content':...}] sorted chronologically.
        """
        with self._get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Fetch recent messages, ordered by newest first
                cur.execute("""
                    SELECT role, content, timestamp FROM interactions 
                    WHERE user_id = %s
                    ORDER BY timestamp DESC
                    LIMIT %s;
                """, (user_id, limit))
                results = cur.fetchall()
                # Reverse to return in chronological order (Oldest -> Newest)
                return results[::-1]
