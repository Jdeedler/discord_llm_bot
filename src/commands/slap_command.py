"""
Slap command handler for the Discord LLM Bot.
Handles the !slap command and dynamically generates AI reactions.
"""

import discord
import logging
from typing import List, Optional

from .base import CommandHandler
from ..utils.config import PERSONALITIES

logger = logging.getLogger(__name__)


class SlapCommand(CommandHandler):
    """Command handler for the !slap command."""

    @property
    def command_name(self) -> str:
        return "slap"

    @property
    def aliases(self) -> List[str]:
        return ["smack", "bonk"]

    @property
    def description(self) -> str:
        return "Slap the AI and get a personality-based reaction."

    async def handle(self, message: discord.Message, args: List[str]) -> None:
        user_id = str(message.author.id)

        # Determine if the message targets the bot or someone else
        mentions_bot = message.guild and message.guild.me in message.mentions
        target = "me" if mentions_bot or not args else " ".join(args)

        # Retrieve and update slap count via memory_manager
        slap_count = self.memory_manager.get_user_metadata(user_id, "slap_count") or 0
        slap_count += 1
        self.memory_manager.set_user_metadata(user_id, "slap_count", slap_count)

        # Get user's personality
        personality = self.memory_manager.get_user_personality(user_id)
        personality_data = PERSONALITIES.get(personality, PERSONALITIES["default"])

        # Modified system prompt for slap response
        system_prompt = (
            personality_data["system_prompt"].strip()
            + "\n\n"
            "The user just slapped you playfully. React in-character with escalating tone based on how many times they’ve done it. "
            f"They have slapped you {slap_count} time(s)."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"*slaps {target}*"}
        ]

        async with message.channel.typing():
            response = self.llm_client.generate_response(messages, personality=personality)
            if response:
                await self.send_response(message, response)
            else:
                logger.warning(f"Fallback slap response for user {user_id}")
                await self.send_response(message, "Ow. That hurt more than usual. 🥲")
