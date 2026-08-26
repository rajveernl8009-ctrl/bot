import discord
from discord.ext import commands
from discord import ui
import os
import asyncio
from flask import Flask
from threading import Thread

# Flask app for keep-alive
app = Flask(__name__)

@app.route('/')
def home():
    return "Verification Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Configuration - CHANGE THESE!
VERIFICATION_CHANNEL_ID = 1542120777464418324  # REPLACE WITH YOUR CHANNEL ID
VERIFIED_ROLE_NAME = "Verified"
LOG_CHANNEL_ID = None  # Optional: set to channel ID for logs

class VerifyButton(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="✅ Verify Me", style=discord.ButtonStyle.success, custom_id="verify_button", emoji="🔐")
    async def verify_button(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        guild = interaction.guild
        role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
        
        if role is None:
            role = await guild.create_role(
                name=VERIFIED_ROLE_NAME,
                reason="Auto-created for verification"
            )
        
        if role in interaction.user.roles:
            await interaction.followup.send("✅ You are already verified!", ephemeral=True)
            return
        
        try:
            await interaction.user.add_roles(role)
            await interaction.followup.send(
                f"✅ You have been successfully verified! Welcome to **{guild.name}**! 🎉",
                ephemeral=True
            )
            
            if LOG_CHANNEL_ID:
                log_channel = bot.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    await log_channel.send(
                        f"✅ **{interaction.user}** ({interaction.user.id}) verified successfully!"
                    )
            
            channel = bot.get_channel(VERIFICATION_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🎉 New Member Verified!",
                    description=f"{interaction.user.mention} has been verified!",
                    color=discord.Color.green()
                )
                await channel.send(embed=embed)
                
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ I don't have permission to give roles! Please contact an admin.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ An error occurred: {str(e)}",
                ephemeral=True
            )

@bot.event
async def on_ready():
    print(f'✅ Bot is online as {bot.user}')
    print(f'Bot ID: {bot.user.id}')
    print(f'Connected to {len(bot.guilds)} guilds')
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="for verification requests"
        )
    )
    
    try:
        channel = bot.get_channel(VERIFICATION_CHANNEL_ID)
        if channel:
            async for message in channel.history(limit=50):
                if message.author == bot.user and message.components:
                    print("✅ Verification message already exists")
                    return
            
            embed = discord.Embed(
                title="🔐 Server Verification",
                description="**Welcome to the server!**\n\n"
                           f"To gain access to the server, please click the **\"✅ Verify Me\"** button below.\n\n"
                           "**Why verify?**\n"
                           "• Prevents bots and spam\n"
                           "• Ensures a safe community\n"
                           "• Unlocks all server channels\n\n"
                           "⚠️ **Note:** This is a one-time verification.",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=bot.user.display_avatar.url)
            embed.set_footer(text=f"🔒 {bot.user.name} • Verification System")
            
            view = VerifyButton()
            await channel.send(embed=embed, view=view)
            print(f"✅ Verification message sent in #{channel.name}")
    except Exception as e:
        print(f"❌ Error sending verification message: {e}")

@bot.event
async def on_member_join(member):
    try:
        channel = bot.get_channel(VERIFICATION_CHANNEL_ID)
        if channel:
            embed = discord.Embed(
                title="👋 Welcome!",
                description=f"Welcome {member.mention}!\n\n"
                           f"Please verify yourself by clicking the **\"✅ Verify Me\"** button below.",
                color=discord.Color.gold()
            )
            await channel.send(embed=embed)
    except Exception as e:
        print(f"Error welcoming new member: {e}")

@bot.command(name='sendverify')
@commands.has_permissions(administrator=True)
async def send_verify(ctx):
    embed = discord.Embed(
        title="🔐 Server Verification",
        description="**Welcome to the server!**\n\n"
                   f"To gain access to the server, please click the **\"✅ Verify Me\"** button below.\n\n"
                   "**Why verify?**\n"
                   "• Prevents bots and spam\n"
                   "• Ensures a safe community\n"
                   "• Unlocks all server channels",
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    embed.set_footer(text=f"🔒 {bot.user.name} • Verification System")
    
    view = VerifyButton()
    await ctx.send(embed=embed, view=view)
    await ctx.send("✅ Verification message sent!", delete_after=5)

@bot.command(name='unverify')
@commands.has_permissions(administrator=True)
async def unverify(ctx, member: discord.Member):
    role = discord.utils.get(ctx.guild.roles, name=VERIFIED_ROLE_NAME)
    if role in member.roles:
        await member.remove_roles(role)
        await ctx.send(f"✅ Removed verification from {member.mention}")
    else:
        await ctx.send(f"❌ {member.mention} is not verified")

@bot.command(name='verifiedcount')
@commands.has_permissions(administrator=True)
async def verified_count(ctx):
    role = discord.utils.get(ctx.guild.roles, name=VERIFIED_ROLE_NAME)
    if role:
        count = len(role.members)
        embed = discord.Embed(
            title="✅ Verification Stats",
            description=f"**Total Verified Members:** {count}\n"
                       f"**Total Server Members:** {ctx.guild.member_count}",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Verified role doesn't exist!")

@bot.command(name='ping')
async def ping(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="🏓 Pong!",
        description=f"Latency: `{latency}ms`",
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid argument. Please try again.")
    else:
        print(f"Error: {error}")

# ============ TOKEN SETUP ============
# Option 1: Get token from environment variable (RECOMMENDED for Render)
# TOKEN = os.environ.get('DISCORD_TOKEN')

# Option 2: Hardcode token (ONLY for testing, NOT recommended for production)
TOKEN = 'MTU0MjA1OTgzODc2NTQwMDEwNg.GXeaO2.NWZd1Eyrj1TUk-tH9lPBcPWU4a8lYXvGHzL_6U'  # Uncomment and add your token here

# Check if token exists
if not TOKEN:
    print("❌ ERROR: DISCORD_TOKEN not found!")
    print("Please set DISCORD_TOKEN environment variable or hardcode it in the script.")
    exit(1)

# Run the bot
keep_alive()
try:
    bot.run(TOKEN)
except discord.LoginFailure:
    print("❌ ERROR: Invalid token! Please check your Discord bot token.")
except Exception as e:
    print(f"❌ ERROR: {e}")
