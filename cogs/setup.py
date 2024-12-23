import discord
from discord.ext import commands
import os
import json
import logging

# Setup logger for debugging and information logs
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Global dictionary to store request channels by guild ID
request_channels = {}

def load_request_channels():
    global request_channels
    # Check if the file exists
    if os.path.exists("request_channels.json"):
        with open("request_channels.json", "r") as f:
            try:
                request_channels = json.load(f)  # Load the request channels data
                logger.info("Loaded request channels: %s", request_channels)
            except json.JSONDecodeError:
                logger.warning("request_channels.json is empty or invalid. Initializing as an empty JSON object.")
                request_channels = {}  # Initialize as an empty dictionary if file is invalid
    else:
        logger.info("No existing request_channels.json found. Initializing as an empty JSON object.")
        request_channels = {}  # Initialize as an empty dictionary if the file doesn't exist

def save_request_channels():
    global request_channels
    # Save the request channels data to the file
    try:
        with open("request_channels.json", "w") as f:
            json.dump(request_channels, f, indent=4)
        logger.info("Saved request channels: %s", request_channels)
    except IOError as e:
        logger.error("Failed to save request channels: %s", e)

class SetupCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        load_request_channels()  # Load request channels when the cog is initialized

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("Setup cog is ready.")

    @discord.app_commands.command(name="setup", description="Set up a channel to receive dragme requests.")
    async def setup(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(embed=discord.Embed(
                title="Permission Denied",
                description="You must have administrator permissions to use this command.",
                color=discord.Color.red()
            ), ephemeral=True)
            return

        guild_id = str(interaction.guild.id)

        # Check if a request channel already exists for this guild
        if guild_id in request_channels:
            existing_channel_id = request_channels[guild_id]
            existing_channel = interaction.guild.get_channel(int(existing_channel_id))
            if existing_channel:
                await interaction.response.send_message(embed=discord.Embed(
                    title="Error",
                    description=f"A request channel is already set up: {existing_channel.mention}",
                    color=discord.Color.red()
                ), ephemeral=True)
                return
            else:
                # If the channel doesn't exist, remove it from the dictionary
                logger.warning(f"Request channel {existing_channel_id} not found. Removing from saved data.")
                del request_channels[guild_id]
                save_request_channels()

        if not interaction.guild.me.guild_permissions.manage_channels:
            await interaction.response.send_message(embed=discord.Embed(
                title="Error",
                description="I do not have permission to manage channels.",
                color=discord.Color.red()
            ), ephemeral=True)
            return

        try:
            # Create a new request channel if none exists
            request_channel = await interaction.guild.create_text_channel("drag-requests")
            request_channels[guild_id] = str(request_channel.id)  # Save as string
            save_request_channels()  # Save the new request channel data
            await interaction.response.send_message(embed=discord.Embed(
                title="Setup Complete",
                description=f"Request channel {request_channel.mention} has been created successfully!",
                color=discord.Color.green()
            ))
        except discord.HTTPException as e:
            await interaction.response.send_message(embed=discord.Embed(
                title="Error",
                description=f"Failed to create the request channel: {e}",
                color=discord.Color.red()
            ), ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(embed=discord.Embed(
                title="Unexpected Error",
                description=f"An error occurred: {e}",
                color=discord.Color.red()
            ), ephemeral=True)

async def setup(bot):
    await bot.add_cog(SetupCog(bot))
