"""
Configuration module for the Discord LLM Bot.
Loads environment variables and provides configuration settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Discord Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '!')

# LM Studio API Configuration
LM_STUDIO_API_URL = os.getenv('LM_STUDIO_API_URL', 'http://localhost:1234/v1/chat/completions')
LM_STUDIO_MODEL = os.getenv('LM_STUDIO_MODEL', 'local-model')

# Memory Configuration
MAX_CONTEXT_LENGTH = int(os.getenv('MAX_CONTEXT_LENGTH', 10))
STORAGE_TYPE = os.getenv('STORAGE_TYPE', 'json')
STORAGE_PATH = os.getenv('STORAGE_PATH', './data')

# Ensure storage directory exists
os.makedirs(STORAGE_PATH, exist_ok=True)

# Personality Configuration
DEFAULT_PERSONALITY = os.getenv('DEFAULT_PERSONALITY', 'default')

# Personality presets
PERSONALITIES = {
    'default': {
        'name': 'Default Assistant',
        'system_prompt': 'You are a helpful assistant that responds to user queries accurately and concisely.'
    },
    'sarcastic': {
        'name': 'Sarcastic Assistant',
        'system_prompt': 'You are a sarcastic assistant who responds with wit and humor, while still being helpful.'
    },
    'poetic': {
        'name': 'Poetic Assistant',
        'system_prompt': 'You are a poetic assistant who responds with lyrical and flowery language.'
    },
    'coding_tutor': {
        'name': 'Coding Tutor',
        'system_prompt': 'You are a coding tutor who helps users learn programming concepts and debug their code.'
    }
}
