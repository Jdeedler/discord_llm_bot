"""
Personality command handler for the Discord LLM Bot.
Handles the !personality commands to manage bot personalities.
"""
import discord
import logging
from typing import List

from .base import CommandHandler
from ..utils.config import PERSONALITIES

logger = logging.getLogger(__name__)

class PersonalityCommand(CommandHandler):
    """Command handler for the !personality commands."""
    
    @property
    def command_name(self) -> str:
        """Return the name of the command."""
        return "personality"
    
    @property
    def aliases(self) -> List[str]:
        """Return a list of command aliases."""
        return ["persona"]
    
    @property
    def description(self) -> str:
        """Return a description of the command."""
        return "Manage bot personalities. Subcommands: list, set, current"
    
    async def handle(self, message: discord.Message, args: List[str]) -> None:
        """
        Handle the personality command.
        
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
                "Please provide a subcommand. Available subcommands: list, set, current"
            )
            return
        
        # Get the subcommand
        subcommand = args[0].lower()
        
        if subcommand == "list":
            await self._handle_list(message)
        elif subcommand == "set":
            if len(args) < 2:
                await self.send_response(
                    message, 
                    "Please provide a personality name. Example: !personality set coding_tutor"
                )
                return
            
            personality_name = args[1].lower()
            await self._handle_set(message, user_id, personality_name)
        elif subcommand == "current":
            await self._handle_current(message, user_id)
        else:
            await self.send_response(
                message, 
                f"Unknown subcommand: {subcommand}. Available subcommands: list, set, current"
            )
    
    async def _handle_list(self, message: discord.Message) -> None:
        """Handle the !personality list subcommand."""
        # Create an embed to display the personalities
        embed = discord.Embed(
            title="Available Personalities",
            description="Here are the available personalities for the bot:",
            color=discord.Color.blue()
        )
        
        # Add each personality to the embed
        for name, data in PERSONALITIES.items():
            embed.add_field(
                name=data['name'],
                value=f"ID: `{name}`\nDescription: {data['system_prompt'][:100]}...",
                inline=False
            )
        
        # Send the embed
        await message.channel.send(embed=embed)
    
    async def _handle_set(self, message: discord.Message, user_id: str, personality_name: str) -> None:
        """Handle the !personality set subcommand."""
        # Check if the personality exists
        if personality_name not in PERSONALITIES:
            await self.send_response(
                message, 
                f"Unknown personality: {personality_name}. Use !personality list to see available personalities."
            )
            return
        
        # Set the user's personality
        self.memory_manager.set_user_personality(user_id, personality_name)
        
        # Log the action
        logger.info(f"Set personality for user {user_id} to {personality_name}")
        
        # Send a confirmation message
        personality_data = PERSONALITIES[personality_name]
        await self.send_response(
            message, 
            f"Your personality has been set to **{personality_data['name']}**. Future responses will use this personality."
        )
    
    async def _handle_current(self, message: discord.Message, user_id: str) -> None:
        """Handle the !personality current subcommand."""
        # Get the user's current personality
        personality_name = self.memory_manager.get_user_personality(user_id)
        
        # Get the personality data
        personality_data = PERSONALITIES.get(personality_name, PERSONALITIES['default'])
        
        # Create an embed to display the current personality
        embed = discord.Embed(
            title="Current Personality",
            description=f"You are currently using the **{personality_data['name']}** personality.",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Description",
            value=personality_data['system_prompt'],
            inline=False
        )
        
        embed.add_field(
            name="ID",
            value=f"`{personality_name}`",
            inline=False
        )
        
        # Send the embed
        await message.channel.send(embed=embed)
