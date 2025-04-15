"""
Memory management module for the Discord LLM Bot.
Handles conversation history storage and retrieval.
"""
import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any

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
                    "INSERT INTO users (user_id, personality, created_at, updated_at) VALUES (?, 'default', ?, ?)",
                    (user_id, now, now)
                )
                self.conn.commit()
                return 'default'
        else:
            data = self._get_json_data()
            if user_id not in data:
                data[user_id] = {
                    'personality': 'default',
                    'messages': [],
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
                    "INSERT INTO users (user_id, personality, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (user_id, personality, now, now)
                )
            
            self.conn.commit()
        else:
            data = self._get_json_data()
            
            if user_id not in data:
                data[user_id] = {
                    'personality': personality,
                    'messages': [],
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
            else:
                data[user_id]['personality'] = personality
                data[user_id]['updated_at'] = datetime.now().isoformat()
            
            self._save_json_data(data)
    
    def add_message(self, user_id: str, role: str, content: str) -> None:
        """Add a message to the user's conversation history."""
        now = datetime.now().isoformat()
        
        if self.storage_type == 'sqlite':
            # Ensure user exists
            self.cursor.execute(
                "SELECT user_id FROM users WHERE user_id = ?", 
                (user_id,)
            )
            if not self.cursor.fetchone():
                self.cursor.execute(
                    "INSERT INTO users (user_id, personality, created_at, updated_at) VALUES (?, 'default', ?, ?)",
                    (user_id, now, now)
                )
            
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
                    'personality': 'default',
                    'messages': [],
                    'created_at': now,
                    'updated_at': now
                }
            
            data[user_id]['messages'].append({
                'role': role,
                'content': content,
                'timestamp': now
            })
            
            # Trim to max context length
            if len(data[user_id]['messages']) > MAX_CONTEXT_LENGTH:
                data[user_id]['messages'] = data[user_id]['messages'][-MAX_CONTEXT_LENGTH:]
            
            data[user_id]['updated_at'] = now
            self._save_json_data(data)
    
    def get_conversation_history(self, user_id: str) -> List[Dict[str, str]]:
        """Get the conversation history for a user."""
        if self.storage_type == 'sqlite':
            self.cursor.execute(
                "SELECT role, content FROM messages WHERE user_id = ? ORDER BY timestamp ASC",
                (user_id,)
            )
            return [{'role': role, 'content': content} for role, content in self.cursor.fetchall()]
        else:
            data = self._get_json_data()
            
            if user_id not in data:
                return []
            
            return [{'role': msg['role'], 'content': msg['content']} for msg in data[user_id]['messages']]
    
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
