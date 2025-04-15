"""
LLM integration module for the Discord LLM Bot.
Handles communication with the LM Studio API.
"""
import json
import logging
import requests
from typing import Dict, List, Optional, Any

from ..utils.config import LM_STUDIO_API_URL, LM_STUDIO_MODEL, PERSONALITIES

logger = logging.getLogger(__name__)

class LLMClient:
    """Client for interacting with the LM Studio API."""
    
    def __init__(self, api_url: Optional[str] = None, model: Optional[str] = None):
        """Initialize the LLM client with API URL and model name."""
        self.api_url = api_url or LM_STUDIO_API_URL
        self.model = model or LM_STUDIO_MODEL
    
    def generate_response(self, messages: List[Dict[str, str]], 
                          personality: str = 'default',
                          temperature: float = 0.7,
                          max_tokens: int = 1000) -> Optional[str]:
        """
        Generate a response from the LLM based on the conversation history.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            personality: Personality to use for the system prompt
            temperature: Controls randomness (0.0 to 1.0)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            Generated response text or None if an error occurred
        """
        # Get the system prompt for the specified personality
        personality_data = PERSONALITIES.get(personality, PERSONALITIES['default'])
        system_prompt = personality_data['system_prompt']
        
        # Prepend system message if not already present
        if not messages or messages[0].get('role') != 'system':
            messages.insert(0, {'role': 'system', 'content': system_prompt})
        
        # Prepare the request payload
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
                timeout=60  # 60 second timeout
            )
            
            # Check if the request was successful
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            logger.debug(f"Received response from LLM API: {json.dumps(result)}")
            
            # Extract the generated text
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
