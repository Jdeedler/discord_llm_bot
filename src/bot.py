"""
Main bot file for the Discord LLM Bot.
Initializes and runs the Discord bot.
"""
import asyncio
import discord
import logging
import os
import sys
from discord.ext import commands
from typing import Dict, List, Optional, Any

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import DISCORD_TOKEN, COMMAND_PREFIX
from src.utils.logging_utils import setup_logger
from src.models.memory import MemoryManager
from src.models.llm import LLMClient

# Set up logging
logger = setup_logger()

# Initialize Discord client with intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=intents)

# Initialize memory manager and LLM client
memory_manager = MemoryManager()
llm_client = LLMClient()

# Dictionary to store command handlers
command_handlers = {}

async def load_commands():
    """Load all command handlers from the commands directory."""
    from src.commands.ask_command import AskCommand
    from src.commands.reset_command import ResetCommand
    from src.commands.personality_command import PersonalityCommand
    from src.commands.memory_command import MemoryCommand
    from src.commands.slap_command import SlapCommand
    
    # Initialize command handlers
    handlers = [
        AskCommand(memory_manager, llm_client),
        ResetCommand(memory_manager, llm_client),
        PersonalityCommand(memory_manager, llm_client),
        MemoryCommand(memory_manager, llm_client),
        SlapCommand(memory_manager, llm_client)
    ]
    
    # Register command handlers
    for handler in handlers:
        command_handlers[handler.command_name] = handler
        for alias in handler.aliases:
            command_handlers[alias] = handler
        
        logger.info(f"Registered command: {handler.command_name}")

@bot.event
async def on_ready():
    """Event handler for when the bot is ready."""
    logger.info(f"Logged in as {bot.user.name} ({bot.user.id})")
    logger.info(f"Using command prefix: {COMMAND_PREFIX}")
    
    # Load commands
    await load_commands()
    
    # Set bot status
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, 
        name=f"{COMMAND_PREFIX}ask"
    ))
    
    logger.info("Bot is ready!")

@bot.event
async def on_message(message):
    """Event handler for when a message is received."""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Check if the message mentions the bot or starts with a command prefix
    is_mentioned = bot.user in message.mentions
    has_prefix = message.content.startswith(COMMAND_PREFIX)
    
    if not (is_mentioned or has_prefix):
        return
    
    # Log the message
    logger.info(f"Message from {message.author}: {message.content}")
    
    # Parse the command
    if is_mentioned and not has_prefix:
        # If the bot is mentioned but no command prefix, treat as !ask
        content = message.content.replace(f'<@{bot.user.id}>', '').strip()
        command = 'ask'
        args = [content] if content else []
    else:
        # Parse command from message
        parts = message.content[len(COMMAND_PREFIX):].strip().split(' ', 1)
        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        # If args is a single string, split it into a list
        if args and isinstance(args[0], str):
            args = args[0].split()
    
    # Handle the command
    if command in command_handlers:
        try:
            await command_handlers[command].handle(message, args)
        except Exception as e:
            logger.error(f"Error handling command {command}: {str(e)}", exc_info=True)
            await message.channel.send(f"Error processing command: {str(e)}")
    else:
        # Unknown command
        await message.channel.send(
            f"Unknown command: {command}. Try {COMMAND_PREFIX}ask <message> to talk to me."
        )

@bot.event
async def on_error(event, *args, **kwargs):
    """Event handler for when an error occurs."""
    logger.error(f"Error in event {event}", exc_info=sys.exc_info())

def main():
    """Main entry point for the bot."""
    try:
        # logging.basicConfig(level=logging.DEBUG)
        logger.info("Starting bot...")
        bot.run(DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.error("Invalid Discord token. Please check your .env file.")
    except Exception as e:
        logger.error(f"Error starting bot: {str(e)}", exc_info=True)
    finally:
        # Clean up resources
        if memory_manager:
            memory_manager.close()
        logger.info("Bot shutdown complete.")

if __name__ == "__main__":
    main()
