import discord
from discord.ext import commands
import logging
import os
from dotenv import load_dotenv
from keep_alive import keep_alive  # Flask server to keep bot alive if needed

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not DISCORD_TOKEN:
    raise ValueError("No DISCORD_TOKEN found in .env file")

# Set up logging
logging.basicConfig(filename='bot.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Intents setup
intents = discord.Intents.default()
intents.members = True
intents.message_content = True  # Enable Message Content Intent

bot = commands.Bot(command_prefix="!", intents=intents)

# List of cogs to load
cogs = [
    "cogs.status_changer",
    "cogs.setup",  # Ensure setup cog is included
    "cogs.dragme",
    "cogs.AvatarBannerUpdater" # Other cogs
]

async def load_cogs():
    """Load all specified cogs."""
    for cog in cogs:
        try:
            if cog in bot.extensions:
                await bot.unload_extension(cog)
            await bot.load_extension(cog)
            logging.info(f"{cog} has been loaded.")
        except Exception as error:
            logging.error(f"Error loading {cog}: {error}")

@bot.event
async def on_ready():
    """When the bot is ready, print the bot info, sync commands, and list registered commands."""
    print(f'Logged in as {bot.user}')

    # Load cogs before syncing commands
    await load_cogs()

    # Sync slash commands with Discord
    try:
        # Sync globally
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")

    except Exception as e:
        print(f"Error syncing commands: {e}")
        logging.error(f"Error syncing commands: {e}")

    # Print all registered slash commands (this helps you debug if they are synced correctly)
    print("Registered slash commands:")
    for command in bot.tree.get_commands():
        print(f"- {command.name}")

# Start Flask (if you want to keep the bot alive on platforms like Replit)
keep_alive()

# Start the bot
bot.run(DISCORD_TOKEN)

