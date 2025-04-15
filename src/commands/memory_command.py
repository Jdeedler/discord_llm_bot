"""
Memory command handler for the Discord LLM Bot.
Handles the !memory commands to manage conversation memory.
"""
import discord
import logging
from typing import List, Dict

from .base import CommandHandler

logger = logging.getLogger(__name__)

class MemoryCommand(CommandHandler):
    """Command handler for the !memory commands."""
    
    @property
    def command_name(self) -> str:
        """Return the name of the command."""
        return "memory"
    
    @property
    def aliases(self) -> List[str]:
        """Return a list of command aliases."""
        return ["mem", "context"]
    
    @property
    def description(self) -> str:
        """Return a description of the command."""
        return "Manage conversation memory. Subcommands: view, delete"
    
    async def handle(self, message: discord.Message, args: List[str]) -> None:
        """
        Handle the memory command.
        
        Args:
            message: The Discord message that triggered the command
            args: List of command arguments
        """
        # Get the user ID
        user_id = str(message.author.id)
        
        # Check if there's a subcommand
        if not args:
            await self.send_response(
                message, 
                "Please provide a subcommand. Available subcommands: view, delete"
            )
            return
        
        # Get the subcommand
        subcommand = args[0].lower()
        
        if subcommand == "view":
            await self._handle_view(message, user_id)
        elif subcommand == "delete":
            await self._handle_delete(message, user_id)
        else:
            await self.send_response(
                message, 
                f"Unknown subcommand: {subcommand}. Available subcommands: view, delete"
            )
    
    async def _handle_view(self, message: discord.Message, user_id: str) -> None:
        """Handle the !memory view subcommand."""
        # Get the conversation history
        conversation_history = self.memory_manager.get_conversation_history(user_id)
        
        if not conversation_history:
            await self.send_response(
                message, 
                "You don't have any conversation history yet. Try talking to me with !ask first!"
            )
            return
        
        # Format the conversation history
        formatted_history = self._format_conversation_history(conversation_history)
        
        # Create an embed to display the conversation history
        embed = discord.Embed(
            title="Your Conversation Memory",
            description="Here's what I remember from our conversation:",
            color=discord.Color.blue()
        )
        
        # Add the conversation history to the embed
        # Discord has a 1024 character limit for embed field values
        # Split into multiple fields if necessary
        chunks = self._split_text(formatted_history, 1000)
        
        for i, chunk in enumerate(chunks):
            embed.add_field(
                name=f"Memory Part {i+1}" if i > 0 else "Memory",
                value=chunk,
                inline=False
            )
        
        # Send the embed
        await message.channel.send(embed=embed)
    
    async def _handle_delete(self, message: discord.Message, user_id: str) -> None:
        """Handle the !memory delete subcommand."""
        # Delete the user's data
        self.memory_manager.delete_user_data(user_id)
        
        # Log the action
        logger.info(f"Deleted memory for user {user_id}")
        
        # Send a confirmation message
        await self.send_response(
            message, 
            "Your conversation memory has been deleted. All your data has been removed from the bot."
        )
    
    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format the conversation history for display."""
        formatted = []
        
        for message in history:
            role = message['role']
            content = message['content']
            
            if role == 'system':
                # Skip system messages
                continue
            elif role == 'user':
                formatted.append(f"**You:** {content}")
            elif role == 'assistant':
                formatted.append(f"**Bot:** {content}")
        
        return "\n\n".join(formatted)
    
    def _split_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks of specified size."""
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
