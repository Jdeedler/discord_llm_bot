"""
Command handler base module for the Discord LLM Bot.
Provides the base class for command handlers.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

import discord

from ..models.memory import MemoryManager
from ..models.llm import LLMClient

logger = logging.getLogger(__name__)

class CommandHandler(ABC):
    """Base class for command handlers."""
    
    def __init__(self, memory_manager: MemoryManager, llm_client: LLMClient):
        """Initialize the command handler with memory manager and LLM client."""
        self.memory_manager = memory_manager
        self.llm_client = llm_client
    
    @property
    @abstractmethod
    def command_name(self) -> str:
        """Return the name of the command."""
        pass
    
    @property
    def aliases(self) -> List[str]:
        """Return a list of command aliases."""
        return []
    
    @property
    def description(self) -> str:
        """Return a description of the command."""
        return "No description provided."
    
    @abstractmethod
    async def handle(self, message: discord.Message, args: List[str]) -> None:
        """
        Handle the command.
        
        Args:
            message: The Discord message that triggered the command
            args: List of command arguments
        """
        pass
    
    async def send_response(self, message: discord.Message, content: str, 
                           embed: Optional[discord.Embed] = None) -> None:
        """
        Send a response to the channel where the command was invoked.
        
        Args:
            message: The Discord message to respond to
            content: The content of the response
            embed: Optional embed to include in the response
        """
        try:
            # Split message if it exceeds Discord's character limit
            if len(content) > 2000:
                chunks = [content[i:i+1990] for i in range(0, len(content), 1990)]
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        await message.channel.send(chunk, embed=embed if i == 0 else None)
                    else:
                        await message.channel.send(chunk)
            else:
                await message.channel.send(content, embed=embed)
        except discord.DiscordException as e:
            logger.error(f"Error sending message: {str(e)}")
            try:
                await message.channel.send("Error sending response. Please try again later.")
            except:
                pass
