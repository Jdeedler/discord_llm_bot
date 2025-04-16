"""
LLM integration module for the Discord LLM Bot.
Handles communication with the LM Studio API and optionally Google's Gemini API.
"""
import json
import logging
import os
import requests
from typing import Dict, List, Optional, Any

from ..utils.config import LM_STUDIO_API_URL, LM_STUDIO_MODEL, PERSONALITIES

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"


class LLMClient:
    """Client for interacting with the LM Studio API or Gemini API."""
    
    def __init__(self, api_url: Optional[str] = None, model: Optional[str] = None):
        self.api_url = api_url or LM_STUDIO_API_URL
        self.model = model or LM_STUDIO_MODEL

    def _try_gemini(self, messages: List[Dict[str, str]]) -> Optional[str]:
        if not GEMINI_API_KEY:
            return None  # Gemini is not configured

        try:
            prompt = "\n".join(f"{m['role'].capitalize()}: {m['content']}" for m in messages)
            payload = {
                "contents": [
                    {"parts": [{"text": prompt}]}
                ]
            }
            params = {"key": GEMINI_API_KEY}
            headers = {"Content-Type": "application/json"}

            logger.debug(f"Sending request to Gemini API: {json.dumps(payload)}")

            response = requests.post(
                GEMINI_API_URL, headers=headers, params=params, json=payload, timeout=60
            )
            response.raise_for_status()
            result = response.json()

            logger.debug(f"Received response from Gemini API: {json.dumps(result)}")

            return result["candidates"][0]["content"]["parts"][0]["text"]

        except Exception as e:
            logger.error(f"Error using Gemini API: {e}")
            return None

    def _enhance_system_prompt_with_usernames(
        self, 
        system_prompt: str, 
        personality_name: str,
        personality_display_name: str,
        current_username: Optional[str] = None,
        user_mapping: Optional[Dict[str, str]] = None,
        is_new_user: bool = False
    ) -> str:
        """
        Enhance the system prompt with personality name, username information, and new user status.
        
        Args:
            system_prompt: The original system prompt
            personality_name: The ID of the personality (e.g., 'coding_tutor')
            personality_display_name: The display name of the personality (e.g., 'Coding Tutor')
            current_username: The username of the current user
            user_mapping: Dictionary mapping user IDs to usernames
            is_new_user: Flag indicating if the user is new
            
        Returns:
            Enhanced system prompt with personality name, username information, and new user context
        """
        # Start with the personality name
        enhanced_prompt = f"Personality: {personality_display_name}\n\n{system_prompt}"
        
        if is_new_user:
            enhanced_prompt += "\n\nThis is a new user. Provide a brief welcome message before addressing their query."
        
        if current_username:
            enhanced_prompt += f"\n\nThe current user you're talking to is named {current_username}."
        
        if user_mapping and len(user_mapping) > 0:
            user_info = "\n\nOther users in the conversation include:"
            for user_id, name in user_mapping.items():
                user_info += f"\n- User {user_id}: {name}"
            
            enhanced_prompt += user_info
            enhanced_prompt += "\n\nWhen responding, you can reference users by their names rather than their IDs."
        
        return enhanced_prompt

    def generate_response(
        self,
        messages: List[Dict[str, str]],
        personality: str = 'default',
        temperature: float = 0.7,
        max_tokens: int = 1000,
        global_context: Optional[Dict[str, List[Dict[str, str]]]] = None,
        current_user_id: Optional[str] = None,
        current_username: Optional[str] = None,
        user_mapping: Optional[Dict[str, str]] = None,
        is_new_user: bool = False
    ) -> Optional[str]:
        """
        Generate a response from the LLM using either Gemini or LM Studio.
        Optionally includes global conversation context, user information, and new user status.
        
        Args:
            messages: List of conversation messages
            personality: Personality to use for response
            temperature: Temperature parameter for response generation
            max_tokens: Maximum tokens in the response
            global_context: Dictionary of all conversations by user_id
            current_user_id: The ID of the current user
            current_username: The username of the current user
            user_mapping: Dictionary mapping user IDs to usernames
            is_new_user: Flag indicating if the user is new
            
        Returns:
            Generated response text
        """
        personality_data = PERSONALITIES.get(personality, PERSONALITIES['default'])
        system_prompt = personality_data['system_prompt']
        personality_display_name = personality_data['name']
        
        # Add personality name, username information, and new user status to the system prompt
        system_prompt = self._enhance_system_prompt_with_usernames(
            system_prompt, 
            personality,
            personality_display_name,
            current_username,
            user_mapping,
            is_new_user
        )

        # Ensure the new personality's system prompt is at the beginning
        messages = [msg for msg in messages if msg.get('role') != 'system']  # Remove existing system messages
        messages.insert(0, {'role': 'system', 'content': system_prompt})

        # Construct a shared context block if provided, excluding system messages
        if global_context:
            shared_messages = []
            for uid, history in global_context.items():
                if uid == current_user_id:
                    continue
                if not history:
                    continue
                # Include username if available
                username = user_mapping.get(uid, f"user {uid}") if user_mapping else f"user {uid}"
                shared_messages.append({'role': 'system', 'content': f"[Context from {username}]"})
                # Only include user and assistant messages from history
                for msg in history[-3:]:
                    if msg.get('role') in ['user', 'assistant']:
                        shared_messages.append(msg)
            
            logger.debug(f"Shared context messages: {json.dumps(shared_messages, indent=2)}")
            messages = shared_messages + messages

        # Try Gemini API first
        gemini_result = self._try_gemini(messages)
        if gemini_result:
            return gemini_result

        # Fall back to LM Studio
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens
        }

        try:
            logger.debug(f"Sending request to LLM API: {json.dumps(payload)}")
            response = requests.post(
                self.api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Received response from LLM API: {json.dumps(result)}")

            if 'choices' in result and len(result['choices']) > 0:
                message = result['choices'][0].get('message', {})
                return message.get('content', '')
            else:
                logger.error(f"Unexpected response format: {result}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Error communicating with LLM API: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing LLM API response: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in LLM client: {str(e)}")
            return None