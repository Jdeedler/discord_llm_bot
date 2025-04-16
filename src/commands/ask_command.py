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
        user_id = str(message.author.id)
        username = message.author.display_name or message.author.name
        
        # Check if this is a new user
        is_new_user = not self.memory_manager.user_exists(user_id)
        
        if not args:
            await self.send_response(
                message,
                "Please provide a message to send to the LLM. Example: !ask What is the capital of France?"
            )
            return

        user_message = " ".join(args)
        
        # Format message differently for new users to clearly identify them
        formatted_message = user_message
        if is_new_user:
            # Initialize the new user before adding any messages
            self.memory_manager.initialize_user(user_id, username)
            logger.info(f"New user initialized: {user_id} ({username})")
            
            # Special formatting for the first message
            formatted_message = f"[NEW USER {username}]: {user_message}"

        # Add user's message to memory
        self.memory_manager.add_message(user_id, "user", formatted_message, username=username)
        
        # Get personality and conversation history AFTER adding the current message
        personality = self.memory_manager.get_user_personality(user_id)
        conversation_history = self.memory_manager.get_conversation_history(user_id)

        async with message.channel.typing():
            try:
                # Ensure username is in the mapping
                user_mapping = self.memory_manager.get_all_usernames()
                if user_id not in user_mapping:
                    user_mapping[user_id] = username
                    
                # Pull global context
                global_context = self.memory_manager.get_all_conversations()
                
                # Generate response - note that the formatted message is already in conversation_history
                llm_response = self.llm_client.generate_response(
                    messages=conversation_history,
                    personality=personality,
                    global_context=global_context,
                    current_user_id=user_id,
                    current_username=username,
                    user_mapping=user_mapping,
                    is_new_user=is_new_user  # Flag to indicate new user status
                )

                if llm_response:
                    self.memory_manager.add_message(user_id, "assistant", llm_response)
                    await self.send_response(message, llm_response)
                else:
                    await self.send_response(
                        message,
                        "Sorry, I couldn't generate a response. Please try again later."
                    )
                    logger.error(f"Failed to generate response for user {user_id} ({username})")

            except Exception as e:
                logger.exception(f"Error handling ask command for user {user_id} ({username}): {e}")
                await self.send_response(
                    message,
                    "An unexpected error occurred while generating the response."
                )