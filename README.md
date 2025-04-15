# Discord LLM Bot

A modular Discord bot in Python that connects to a locally-hosted LLM running via LM Studio. The bot forwards user prompts to the LLM, receives responses, and posts them back to Discord. It supports user-controlled memory/context management and personality switching.

## Features

- Integration with LM Studio via its local HTTP API
- Persistent memory per user (stored in JSON or SQLite)
- Personality switching system
- Modular command handler for easy extension

### Commands

- `!ask <message>` - Sends message to the LLM and returns response
- `!reset` - Wipes conversation history/context for that user
- `!personality list` - Lists available personalities
- `!personality set <name>` - Sets personality for future responses
- `!personality current` - Shows currently active personality
- `!memory view` - Displays current conversation memory
- `!memory delete` - Deletes saved memory/context for the user

## Setup

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a Discord bot and get your token:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Go to the "Bot" tab and create a bot
   - Copy the token
   - Enable "Message Content Intent" under Privileged Gateway Intents

4. Configure your environment:
   - Copy `.env.example` to `.env`
   - Add your Discord token and configure other settings

5. Start LM Studio:
   - Launch LM Studio
   - Load your preferred model
   - Start the local server (default: http://localhost:1234)

6. Run the bot:
   ```
   python src/bot.py
   ```

## Configuration

The bot can be configured using the `.env` file or by editing `config.py`. Available settings include:

- Discord token
- LM Studio API endpoint
- Default personality
- Memory storage options
- Context window size

## Extending the Bot

The bot is designed to be modular and easily extensible:

1. Add new commands by creating files in the `commands` directory
2. Create new personalities by adding them to the personalities configuration
3. Extend memory management by modifying the `models/memory.py` file

## License

MIT
