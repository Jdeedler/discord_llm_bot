"""
Ask command handler for the Discord LLM Bot.
Handles the !ask command to interact with the LLM.
"""
import discord
import logging
from typing import List

from .base import CommandHandler

logger = logging.getLogger(__name__)

class AskCommand(CommandHandler):
    """Command handler for the !ask command."""
    
    @property
    def command_name(self) -> str:
        """Return the name of the command."""
        return "ask"
    
    @property
    def aliases(self) -> List[str]:
        """Return a list of command aliases."""
        return ["chat", "talk"]
    
    @property
    def description(self) -> str:
        """Return a description of the command."""
        return "Send a message to the LLM and get a response."
    
    async def handle(self, message: discord.Message, args: List[str]) -> None:
        """
        Handle the ask command.
        
        Args:
            message: The Discord message that triggered the command
            args: List of command arguments (the message to send to the LLM)
        """
        # Get the user ID
        user_id = str(message.author.id)
        
        # Check if there's a message to send
        if not args:
            await self.send_response(
                message, 
                "Please provide a message to send to the LLM. Example: !ask What is the capital of France?"
            )
            return
        
        # Join the arguments into a single message
        user_message = " ".join(args)
        
        # Get the user's personality
        personality = self.memory_manager.get_user_personality(user_id)
        
        # Get the conversation history
        conversation_history = self.memory_manager.get_conversation_history(user_id)
        
        # Add the user's message to the conversation history
        self.memory_manager.add_message(user_id, "user", user_message)
        
        # Send a typing indicator to show the bot is processing
        async with message.channel.typing():
            # Generate a response from the LLM
            llm_response = self.llm_client.generate_response(
                conversation_history + [{"role": "user", "content": user_message}],
                personality=personality
            )
            
            if llm_response:
                # Add the LLM's response to the conversation history
                self.memory_manager.add_message(user_id, "assistant", llm_response)
                
                # Send the response to the user
                await self.send_response(message, llm_response)
            else:
                # If there was an error generating a response
                await self.send_response(
                    message, 
                    "Sorry, I couldn't generate a response. Please try again later."
                )
                logger.error(f"Failed to generate response for user {user_id}")
