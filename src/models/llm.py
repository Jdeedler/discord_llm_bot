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

    def generate_response(self, messages: List[Dict[str, str]],
                          personality: str = 'default',
                          temperature: float = 0.7,
                          max_tokens: int = 1000) -> Optional[str]:
        personality_data = PERSONALITIES.get(personality, PERSONALITIES['default'])
        system_prompt = personality_data['system_prompt']

        if not messages or messages[0].get('role') != 'system':
            messages.insert(0, {'role': 'system', 'content': system_prompt})

        # Try Gemini API first, if available
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
