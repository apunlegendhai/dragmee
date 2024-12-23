import discord
from discord.ext import commands
import logging
from .setup import request_channels  # Import request_channels from the setup file

logger = logging.getLogger(__name__)

# Set logging level to WARNING to reduce verbosity
logging.basicConfig(level=logging.WARNING)
logging.getLogger('discord').setLevel(logging.WARNING)

TIMEOUT_DURATION = 30  # Set timeout duration

class DragmeButtons(discord.ui.View):
    def __init__(self, target_user, interaction_user, target_voice_channel, request_message=None):
        super().__init__(timeout=TIMEOUT_DURATION)  # Initialize the parent class (View) with a timeout
        self.target_user = target_user
        self.interaction_user = interaction_user
        self.target_voice_channel = target_voice_channel
        self.request_message = request_message  # Optional, can be None if not needed

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle the accept button click."""
        if interaction.user != self.target_user:
            await interaction.response.send_message("You are not authorized to accept this request.", ephemeral=True)
            return

        try:
            # Move the user to the target voice channel
            await self.interaction_user.move_to(self.target_voice_channel)
            await interaction.response.send_message(f"{self.interaction_user.mention} has been moved to {self.target_voice_channel.name}.")
        except Exception as e:
            logger.error(f"Error moving {self.interaction_user} to {self.target_voice_channel}: {e}")
            await interaction.response.send_message("There was an error moving the user to the voice channel.")

        # Optionally delete the request message after accepting
        if self.request_message:
            await self.request_message.delete()

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.red)
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle the reject button click."""
        if interaction.user != self.target_user:
            await interaction.response.send_message("You are not authorized to reject this request.", ephemeral=True)
            return

        await interaction.response.send_message(f"{self.interaction_user.mention}'s request has been rejected.")

        # Optionally delete the request message after rejecting
        if self.request_message:
            await self.request_message.delete()

    async def on_timeout(self):
        """Handle the timeout for the view."""
        if self.request_message:
            await self.request_message.edit(content="This request has timed out.", view=None)


class DragmeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        logger.info("DragmeCog initialized.")

    async def check_permissions(self, interaction):
        """Check if the bot has necessary permissions to move users."""
        if not interaction.guild.me.guild_permissions.move_members or not interaction.guild.me.guild_permissions.connect:
            await interaction.response.send_message(
                "The bot does not have the necessary permissions to move users into voice channels.",
                ephemeral=True
            )
            return False
        return True

    @commands.cooldown(1, 60, commands.BucketType.user)  # 1 use per 60 seconds per user
    @discord.app_commands.command(name="dragmee", description="Request to be dragged into a user's voice channel.")
    async def dragme(self, interaction: discord.Interaction, target_user: discord.Member):
        """Command to request to join a target user's voice channel."""
        logger.debug(f"Interaction channel ID: {interaction.channel.id}")
        request_channel_id = request_channels.get(str(interaction.guild.id))

        # Check if the interaction is in the correct channel
        if request_channel_id is None or interaction.channel.id != int(request_channel_id):
            await interaction.response.send_message(
                "This command can only be used in the designated drag-requests channel.",
                ephemeral=True
            )
            return

        if not await self.check_permissions(interaction):
            return

        if interaction.user.voice is None:
            await interaction.response.send_message(
                f"{interaction.user.mention}, you must be in a voice channel to use this command.",
                ephemeral=True
            )
            return

        if target_user.voice is None:
            await interaction.response.send_message(
                f"{target_user.mention} is not in a voice channel.",
                ephemeral=True
            )
            return

        target_voice_channel = target_user.voice.channel

        if interaction.user.voice.channel == target_voice_channel:
            await interaction.response.send_message(
                f"{interaction.user.mention}, you are already in {target_user.mention}'s voice channel!",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"Request to join {target_user.mention}'s voice channel has been sent.",
            ephemeral=True
        )

        # Create and send the request message with buttons
        view = DragmeButtons(target_user, interaction.user, target_voice_channel)
        request_message = await interaction.channel.send(
            f"{target_user.mention}, {interaction.user.mention} wants to join your voice channel.",
            view=view
        )

        # Optionally update the view with the request message
        view.request_message = request_message

    @dragme.error
    async def dragme_error(self, interaction: discord.Interaction, error: Exception):
        """Handle errors for the dragme command, including cooldowns."""
        if isinstance(error, commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"Please wait {error.retry_after:.2f} seconds before using this command again.",
                ephemeral=True
            )
        else:
            logger.error(f"An error occurred: {error}")
            await interaction.response.send_message("An unexpected error occurred. Please try again later.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(DragmeCog(bot))
