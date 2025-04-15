"""
Reset command handler for the Discord LLM Bot.
Handles the !reset command to clear conversation history.
"""
import discord
import logging
from typing import List

from .base import CommandHandler

logger = logging.getLogger(__name__)

class ResetCommand(CommandHandler):
    """Command handler for the !reset command."""
    
    @property
    def command_name(self) -> str:
        """Return the name of the command."""
        return "reset"
    
    @property
    def aliases(self) -> List[str]:
        """Return a list of command aliases."""
        return ["clear"]
    
    @property
    def description(self) -> str:
        """Return a description of the command."""
        return "Reset your conversation history with the bot."
    
    async def handle(self, message: discord.Message, args: List[str]) -> None:
        """
        Handle the reset command.
        
        Args:
            message: The Discord message that triggered the command
            args: List of command arguments (not used for this command)
        """
        # Get the user ID
        user_id = str(message.author.id)
        
        # Reset the user's conversation history
        self.memory_manager.reset_user_memory(user_id)
        
        # Log the action
        logger.info(f"Reset conversation history for user {user_id}")
        
        # Send a confirmation message
        await self.send_response(
            message, 
            "Your conversation history has been reset. You're starting with a clean slate!"
        )
