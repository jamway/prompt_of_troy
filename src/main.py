# Import required logging modules for handling log files and configuration
import logging
import logging.handlers
import os
from dotenv import load_dotenv  # For loading environment variables
from bot import discord_client  # Import the Discord bot client

def main():
    """
    Main entry point of the application.
    Sets up logging configuration and starts the Discord bot.
    
    The function:
    1. Configures the root logger for the application
    2. Sets up rotating file handler for log management
    3. Formats log messages with timestamp and level
    4. Starts the Discord bot with token from environment
    """
    # Get the application logger
    logger = logging.getLogger("promptoftroy")
    logger.setLevel(logging.INFO)
    # Configure Discord's HTTP logger
    logging.getLogger("discord.http").setLevel(logging.INFO)
    
    # Set up rotating file handler to manage log files
    handler = logging.handlers.RotatingFileHandler(
    filename="promptoftroy.log",
    encoding="utf-8",
    maxBytes=32 * 1024 * 1024,  # 32 MiB max file size
    backupCount=5,  # Keep 5 backup files before rotating
    )
    
    # Configure timestamp format for log messages
    dt_fmt = "%Y-%m-%d %H:%M:%S"
    # Set up log message format with timestamp, level, logger name
    formatter = logging.Formatter(
        "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
    )
    
    # Apply formatter to handler and add to logger
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Log session start and run Discord bot
    logger.info("Start session")
    discord_client.run(os.getenv("DISCORD_TOKEN"))
    
if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    main()