"""
Memory management module for the Discord LLM Bot.
Handles conversation history storage and retrieval.
"""
import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from ..utils.config import STORAGE_TYPE, STORAGE_PATH, MAX_CONTEXT_LENGTH


class MemoryManager:
    """Manages conversation memory for users."""
    
    def __init__(self):
        """Initialize the memory manager based on configured storage type."""
        self.storage_type = STORAGE_TYPE
        self.storage_path = STORAGE_PATH
        
        if self.storage_type == 'sqlite':
            self._init_sqlite()
        elif self.storage_type == 'json':
            self._init_json()
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")
    
    def _init_sqlite(self):
        """Initialize SQLite database for memory storage."""
        db_path = os.path.join(self.storage_path, 'memory.db')
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Create tables if they don't exist
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            personality TEXT DEFAULT 'default',
            created_at TEXT,
            updated_at TEXT
        )
        ''')
        
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Add a new table for user metadata
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            key TEXT,
            value TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id),
            UNIQUE(user_id, key)
        )
        ''')
        
        self.conn.commit()
    
    def _init_json(self):
        """Initialize JSON file storage for memory."""
        self.json_path = os.path.join(self.storage_path, 'memory.json')
        
        if not os.path.exists(self.json_path):
            with open(self.json_path, 'w') as f:
                json.dump({}, f)
    
    def _get_json_data(self) -> Dict:
        """Load data from JSON file."""
        try:
            with open(self.json_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_json_data(self, data: Dict):
        """Save data to JSON file."""
        with open(self.json_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_user_personality(self, user_id: str) -> str:
        """Get the current personality for a user."""
        if self.storage_type == 'sqlite':
            self.cursor.execute(
                "SELECT personality FROM users WHERE user_id = ?", 
                (user_id,)
            )
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
            else:
                # Create new user with default personality
                now = datetime.now().isoformat()
                self.cursor.execute(
                    "INSERT INTO users (user_id, username, personality, created_at, updated_at) VALUES (?, ?, 'default', ?, ?)",
                    (user_id, f"User_{user_id[:8]}", now, now)
                )
                self.conn.commit()
                return 'default'
        else:
            data = self._get_json_data()
            if user_id not in data:
                data[user_id] = {
                    'username': f"User_{user_id[:8]}",
                    'personality': 'default',
                    'messages': [],
                    'metadata': {},
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                self._save_json_data(data)
            
            return data[user_id]['personality']
    
    def set_user_personality(self, user_id: str, personality: str) -> None:
        """Set the personality for a user."""
        if self.storage_type == 'sqlite':
            now = datetime.now().isoformat()
            self.cursor.execute(
                "UPDATE users SET personality = ?, updated_at = ? WHERE user_id = ?",
                (personality, now, user_id)
            )
            
            if self.cursor.rowcount == 0:
                # User doesn't exist, create new
                self.cursor.execute(
                    "INSERT INTO users (user_id, username, personality, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                    (user_id, f"User_{user_id[:8]}", personality, now, now)
                )
            
            self.conn.commit()
        else:
            data = self._get_json_data()
            
            if user_id not in data:
                data[user_id] = {
                    'username': f"User_{user_id[:8]}",
                    'personality': personality,
                    'messages': [],
                    'metadata': {},
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            else:
                data[user_id]['personality'] = personality
                data[user_id]['updated_at'] = datetime.now().isoformat()
            
            self._save_json_data(data)
    
    def update_username(self, user_id: str, username: str) -> None:
        """Update the username for a user."""
        if self.storage_type == 'sqlite':
            now = datetime.now().isoformat()
            self.cursor.execute(
                "UPDATE users SET username = ?, updated_at = ? WHERE user_id = ?",
                (username, now, user_id)
            )
            
            if self.cursor.rowcount == 0:
                # User doesn't exist, create new
                self.cursor.execute(
                    "INSERT INTO users (user_id, username, personality, created_at, updated_at) VALUES (?, ?, 'default', ?, ?)",
                    (user_id, username, now, now)
                )
            
            self.conn.commit()
        else:
            data = self._get_json_data()
            
            if user_id not in data:
                data[user_id] = {
                    'username': username,
                    'personality': 'default',
                    'messages': [],
                    'metadata': {},
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            else:
                data[user_id]['username'] = username
                data[user_id]['updated_at'] = datetime.now().isoformat()
            
            self._save_json_data(data)
    
    def get_username(self, user_id: str) -> str:
        """Get the username for a user."""
        if self.storage_type == 'sqlite':
            self.cursor.execute(
                "SELECT username FROM users WHERE user_id = ?", 
                (user_id,)
            )
            result = self.cursor.fetchone()
            
            if result:
                return result[0]
            else:
                # Default placeholder username
                return f"User_{user_id[:8]}"
        else:
            data = self._get_json_data()
            
            if user_id in data and 'username' in data[user_id]:
                return data[user_id]['username']
            else:
                return f"User_{user_id[:8]}"
    
    def get_all_usernames(self) -> Dict[str, str]:
        """Get all user IDs and their corresponding usernames."""
        if self.storage_type == 'sqlite':
            self.cursor.execute("SELECT user_id, username FROM users")
            return {user_id: username for user_id, username in self.cursor.fetchall()}
        else:
            data = self._get_json_data()
            return {user_id: user_data.get('username', f"User_{user_id[:8]}") for user_id, user_data in data.items()}
    
    def add_message(self, user_id: str, role: str, content: str, username: Optional[str] = None) -> None:

        """Add a message to the user's conversation history."""
        now = datetime.now().isoformat()
        
        # Update username if provided
        if username:
            self.update_username(user_id, username)
        else:
            username = self.get_username(user_id)
        
        message_obj = {
            'role': role,
            'content': content,
            'timestamp': now,
            'username': username  # Include username in message object
        }
        
        if self.storage_type == 'sqlite':
            # Ensure user exists
            self._ensure_user_exists(user_id, username)
            
            # Add message
            self.cursor.execute(
                "INSERT INTO messages (user_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
                (user_id, role, content, now)
            )
            self.conn.commit()
            
            # Trim to max context length
            self.cursor.execute(
                """
                DELETE FROM messages 
                WHERE id IN (
                    SELECT id FROM messages 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT -1 OFFSET ?
                )
                """,
                (user_id, MAX_CONTEXT_LENGTH)
            )
            self.conn.commit()
        else:
            data = self._get_json_data()
            
            if user_id not in data:
                data[user_id] = {
                    'username': username,
                    'personality': 'default',
                    'messages': [],
                    'metadata': {},
                    'created_at': now,
                    'updated_at': now
                }
            
            data[user_id]['messages'].append(message_obj)
            
            # Trim to max context length
            if len(data[user_id]['messages']) > MAX_CONTEXT_LENGTH:
                data[user_id]['messages'] = data[user_id]['messages'][-MAX_CONTEXT_LENGTH:]
            
            data[user_id]['updated_at'] = now
            self._save_json_data(data)

    def get_conversation_history(self, user_id: str, include_usernames: bool = True) -> List[Dict[str, str]]:
        """Get the conversation history for a user."""
        username = self.get_username(user_id)
        
        if self.storage_type == 'sqlite':
            self.cursor.execute(
                "SELECT role, content FROM messages WHERE user_id = ? ORDER BY timestamp ASC",
                (user_id,)
            )
            messages = [{'role': role, 'content': content} for role, content in self.cursor.fetchall()]
        else:
            data = self._get_json_data()
            
            if user_id not in data:
                return []
            
            messages = [{'role': msg['role'], 'content': msg['content']} for msg in data[user_id]['messages']]
        
        # Only add username info if requested
        if include_usernames and messages:
            # For user messages, include username in content
            for msg in messages:
                if msg['role'] == 'user':
                    if not msg['content'].startswith(f"[{username}]: "):
                        msg['content'] = f"[{username}]: {msg['content']}"
        
        return messages
        
    def get_conversation_with_usernames(self, user_id: str) -> Tuple[str, List[Dict[str, str]]]:
        """Get the conversation history and username for a user."""
        username = self.get_username(user_id)
        history = self.get_conversation_history(user_id)
        return (username, history)
        
    def get_all_conversations(self) -> Dict[str, List[Dict[str, str]]]:
        """Get the full conversation history for all users."""
        if self.storage_type == 'sqlite':
            self.cursor.execute("SELECT user_id, role, content FROM messages ORDER BY timestamp ASC")
            rows = self.cursor.fetchall()
            conversations: Dict[str, List[Dict[str, str]]] = {}
            
            for user_id, role, content in rows:
                if user_id not in conversations:
                    conversations[user_id] = []
                conversations[user_id].append({'role': role, 'content': content})
            
            return conversations
        else:
            data = self._get_json_data()
            return {
                user_id: [{'role': msg['role'], 'content': msg['content']} for msg in user_data.get('messages', [])]
                for user_id, user_data in data.items()
            }
    
    def get_user_metadata(self, user_id: str, key: str) -> Any:
        """Get metadata value for a user."""
        if self.storage_type == 'sqlite':
            # Ensure user exists
            self._ensure_user_exists(user_id)
            
            self.cursor.execute(
                "SELECT value FROM user_metadata WHERE user_id = ? AND key = ?",
                (user_id, key)
            )
            result = self.cursor.fetchone()
            
            if result:
                # Try to parse JSON if possible
                try:
                    return json.loads(result[0])
                except json.JSONDecodeError:
                    return result[0]
            return None
        else:
            data = self._get_json_data()
            
            if user_id not in data:
                return None
            
            if 'metadata' not in data[user_id]:
                data[user_id]['metadata'] = {}
                self._save_json_data(data)
                return None
            
            return data[user_id]['metadata'].get(key)
    
    def set_user_metadata(self, user_id: str, key: str, value: Any) -> None:
        """Set metadata value for a user."""
        if self.storage_type == 'sqlite':
            # Ensure user exists
            self._ensure_user_exists(user_id)
            
            # Convert value to JSON string if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            self.cursor.execute(
                """
                INSERT INTO user_metadata (user_id, key, value) 
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, key) 
                DO UPDATE SET value = ?
                """,
                (user_id, key, value, value)
            )
            self.conn.commit()
        else:
            data = self._get_json_data()
            
            if user_id not in data:
                now = datetime.now().isoformat()
                data[user_id] = {
                    'username': f"User_{user_id[:8]}",
                    'personality': 'default',
                    'messages': [],
                    'metadata': {key: value},
                    'created_at': now,
                    'updated_at': now
                }
            else:
                if 'metadata' not in data[user_id]:
                    data[user_id]['metadata'] = {}
                
                data[user_id]['metadata'][key] = value
                data[user_id]['updated_at'] = datetime.now().isoformat()
            
            self._save_json_data(data)


    def initialize_user(self, user_id: str, username: str) -> None:
        """Initialize a new user in the memory system."""
        now = datetime.now().isoformat()
        
        if self.storage_type == 'sqlite':
            self.cursor.execute(
                "INSERT INTO users (user_id, username, personality, created_at, updated_at) VALUES (?, ?, 'default', ?, ?)",
                (user_id, username, now, now)
            )
            self.conn.commit()
        else:
            data = self._get_json_data()
            data[user_id] = {
                'username': username,
                'personality': 'default',
                'messages': [],
                'metadata': {},
                'created_at': now,
                'updated_at': now
            }
            self._save_json_data(data)

    def user_exists(self, user_id: str) -> bool:
        """Check if user exists in the memory system."""
        if self.storage_type == 'sqlite':
            self.cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
            return bool(self.cursor.fetchone())
        else:
            data = self._get_json_data()
            return user_id in data
    
    def _ensure_user_exists(self, user_id: str, username: Optional[str] = None) -> None:
        """Ensure a user exists in the database."""
        if self.storage_type == 'sqlite':
            self.cursor.execute(
                "SELECT user_id FROM users WHERE user_id = ?", 
                (user_id,)
            )
            if not self.cursor.fetchone():
                now = datetime.now().isoformat()
                self.cursor.execute(
                    "INSERT INTO users (user_id, username, personality, created_at, updated_at) VALUES (?, ?, 'default', ?, ?)",
                    (user_id, username or f"User_{user_id[:8]}", now, now)
                )
                self.conn.commit()
            elif username:
                # Update username if provided
                self.cursor.execute(
                    "UPDATE users SET username = ? WHERE user_id = ?",
                    (username, user_id)
                )
                self.conn.commit()
    
    def reset_user_memory(self, user_id: str) -> None:
        """Reset the conversation history for a user."""
        if self.storage_type == 'sqlite':
            self.cursor.execute(
                "DELETE FROM messages WHERE user_id = ?",
                (user_id,)
            )
            self.conn.commit()
        else:
            data = self._get_json_data()
            
            if user_id in data:
                data[user_id]['messages'] = []
                data[user_id]['updated_at'] = datetime.now().isoformat()
                self._save_json_data(data)
    
    def delete_user_data(self, user_id: str) -> None:
        """Delete all data for a user."""
        if self.storage_type == 'sqlite':
            self.cursor.execute(
                "DELETE FROM messages WHERE user_id = ?",
                (user_id,)
            )
            self.cursor.execute(
                "DELETE FROM user_metadata WHERE user_id = ?",
                (user_id,)
            )
            self.cursor.execute(
                "DELETE FROM users WHERE user_id = ?",
                (user_id,)
            )
            self.conn.commit()
        else:
            data = self._get_json_data()
            
            if user_id in data:
                del data[user_id]
                self._save_json_data(data)
    
    def close(self):
        """Close any open connections."""
        if self.storage_type == 'sqlite':
            self.conn.close()