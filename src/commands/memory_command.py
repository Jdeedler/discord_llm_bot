"""
Memory command handler for the Discord LLM Bot.
Handles the !memory commands to manage conversation memory.
"""
import discord
import logging
from typing import List, Dict
import tempfile
import os

from .base import CommandHandler

logger = logging.getLogger(__name__)

class MemoryCommand(CommandHandler):
    """Command handler for the !memory commands."""
    
    # Discord limits
    EMBED_FIELD_LIMIT = 1000  # Max characters per embed field (buffer from 1024)
    EMBED_TOTAL_LIMIT = 6000  # Max total characters in an embed
    FIELD_COUNT_LIMIT = 25    # Max fields in an embed
    MESSAGE_LIMIT = 2000      # Max characters in a message
    DISPLAY_THRESHOLD = 2000  # Threshold to prefer file output

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
        return "Manage conversation memory. Subcommands: view, delete. Use --embed to force embed output."
    
    async def handle(self, message: discord.Message, args: List[str]) -> None:
        """
        Handle the memory command.
        
        Args:
            message: The Discord message that triggered the command
            args: List of command arguments
        """
        user_id = str(message.author.id)
        
        # Check for --embed flag
        force_embed = "--embed" in args
        if force_embed:
            args.remove("--embed")
        
        # Check if there's a subcommand
        if not args:
            await self.send_response(
                message, 
                "Please provide a subcommand. Available subcommands: view, delete. Use --embed to force embed output."
            )
            return
        
        subcommand = args[0].lower()
        
        if subcommand == "view":
            await self._handle_view(message, user_id, force_embed)
        elif subcommand == "delete":
            await self._handle_delete(message, user_id)
        else:
            await self.send_response(
                message, 
                f"Unknown subcommand: {subcommand}. Available subcommands: view, delete"
            )
    
    async def _handle_view(self, message: discord.Message, user_id: str, force_embed: bool) -> None:
        """Handle the !memory view subcommand."""
        # Get conversation history without username prefixes for file, with for embeds
        history_for_file = self.memory_manager.get_conversation_history(user_id, include_usernames=False)
        history_for_embed = self.memory_manager.get_conversation_history(user_id, include_usernames=True)
        
        if not history_for_file:
            await self.send_response(
                message, 
                "You don't have any conversation history yet. Try talking to me with !ask first!"
            )
            return
        
        # Format histories
        formatted_for_file = self._format_conversation_history(history_for_file)
        formatted_for_embed = self._format_conversation_history(history_for_embed)
        
        # Estimate embed field count
        estimated_fields = len(self._split_text(formatted_for_embed, self.EMBED_FIELD_LIMIT))
        
        # Log the action
        logger.info(f"Viewing memory for user {user_id}, history length: {len(formatted_for_embed)} characters, estimated fields: {estimated_fields}")
        
        # Decide output method
        if force_embed or (len(formatted_for_embed) < self.DISPLAY_THRESHOLD and estimated_fields <= self.FIELD_COUNT_LIMIT):
            await self._send_embed_history(message, formatted_for_embed)
        else:
            try:
                await self._send_file_history(message, formatted_for_file, user_id)
            except Exception as e:
                logger.error(f"Failed to send file for user {user_id}: {str(e)}")
                await self._send_split_embeds(message, formatted_for_embed)
    
    async def _send_embed_history(self, message: discord.Message, formatted_history: str) -> None:
        """Send conversation history in a single embed for small histories."""
        embed = discord.Embed(
            title="Your Conversation Memory",
            description="Here's what I remember from our conversation:",
            color=discord.Color.blue()
        )
        
        # Split into fields
        chunks = self._split_text(formatted_history, self.EMBED_FIELD_LIMIT)
        
        for i, chunk in enumerate(chunks):
            embed.add_field(
                name=f"Memory Part {i+1}" if i > 0 else "Memory",
                value=chunk,
                inline=False
            )
        
        # Check embed limits
        total_length = sum(len(field.value) for field in embed.fields) + len(embed.title) + len(embed.description)
        if total_length > self.EMBED_TOTAL_LIMIT or len(embed.fields) > self.FIELD_COUNT_LIMIT:
            logger.warning(f"Embed for user {message.author.id} exceeds limits, falling back to file")
            await self._send_file_history(message, formatted_history, str(message.author.id))
            return
        
        await message.channel.send(embed=embed)
    
    async def _send_file_history(self, message: discord.Message, formatted_history: str, user_id: str) -> None:
        """Send conversation history as a text file attachment."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', prefix=f'memory_{user_id}_', delete=False, encoding='utf-8') as temp_file:
            temp_file.write(formatted_history)
            temp_file_path = temp_file.name
        
        try:
            embed = discord.Embed(
                title="Your Conversation Memory",
                description="Your conversation history is too long to display here. I've attached it as a text file!",
                color=discord.Color.blue()
            )
            
            file = discord.File(temp_file_path, filename=f"conversation_history_{user_id}.txt")
            await message.channel.send(embed=embed, file=file)
            logger.info(f"Sent memory file for user {user_id}: {temp_file_path}")
        
        finally:
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.error(f"Failed to delete temp file {temp_file_path}: {str(e)}")
    
    async def _send_split_embeds(self, message: discord.Message, formatted_history: str) -> None:
        """Send conversation history in multiple embeds for large histories (fallback)."""
        messages = formatted_history.split("\n\n")
        embeds = []
        current_embed = discord.Embed(
            title="Your Conversation Memory",
            description="Continued conversation history:",
            color=discord.Color.blue()
        )
        current_length = len(current_embed.title) + len(current_embed.description)
        current_fields = 0
        
        for msg in messages:
            # Account for field name (~20 chars) and buffer
            if len(msg) > self.EMBED_FIELD_LIMIT - 20:
                logger.warning(f"Single message too long for user {message.author.id}: {len(msg)} characters")
                continue
            
            field_name = f"Memory Part {current_fields + 1}" if current_fields > 0 else "Memory"
            field_length = len(msg) + len(field_name)
            
            if (current_length + field_length > self.EMBED_TOTAL_LIMIT or 
                current_fields >= self.FIELD_COUNT_LIMIT):
                embeds.append(current_embed)
                current_embed = discord.Embed(
                    title=f"Your Conversation Memory (Continued)",
                    description="Continued conversation history:",
                    color=discord.Color.blue()
                )
                current_length = len(current_embed.title) + len(current_embed.description)
                current_fields = 0
                field_name = "Memory"
            
            current_embed.add_field(name=field_name, value=msg, inline=False)
            current_length += field_length
            current_fields += 1
        
        if current_fields > 0:
            embeds.append(current_embed)
        
        if not embeds:
            await self.send_response(
                message,
                "Your history contains messages too long to display. Please use file output."
            )
            return
        
        for i, embed in enumerate(embeds):
            await message.channel.send(embed=embed)
            logger.info(f"Sent embed {i+1}/{len(embeds)} for user {message.author.id}")
    
    def _format_conversation_history(self, history: List[Dict[str, str]]) -> str:
        """Format the conversation history for display or file output."""
        formatted = []
        
        for message in history:
            role = message['role']
            content = message['content']
            
            if role == 'system':
                continue
            elif role == 'user':
                formatted.append(f"You: {content}")
            elif role == 'assistant':
                formatted.append(f"Bot: {content}")
        
        return "\n\n".join(formatted)
    
    def _split_text(self, text: str, chunk_size: int) -> List[str]:
        """Split text into chunks of specified size."""
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]