import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
from dotenv import load_dotenv
import aiohttp
import re
from urllib.parse import quote
import json

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TOKEN')

# Initialize Flask server for 24/7 uptime
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Discord Bot is Online | Uptime: 100%"

def run_flask():
    app.run(host='0.0.0.0', port=10000)

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Regex for Roblox share links
SHARE_LINK_RE = re.compile(
    r"https?://(?:www\.)?roblox\.com/share\?code=([0-9a-f]{32})&type=Server"
)

# Mobile headers for API requests
MOBILE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
}

@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game(name="!dslink"))

def create_deep_link(code: str):
    """Create modern Roblox deep link"""
    return f"roblox://navigation/share_links?code={code}&type=Server"

@bot.command(name="dslink", help="Convert Roblox share link to private server URL")
async def dslink(ctx, link: str):
    try:
        # Validate link format
        match = SHARE_LINK_RE.fullmatch(link.strip())
        if not match:
            embed = discord.Embed(
                color=discord.Color.red(),
                description="❌ **Invalid link format!**\nExample: `https://www.roblox.com/share?code=abc123...&type=Server`"
            )
            return await ctx.send(embed=embed)

        code = match.group(1)
        share_url = f"https://www.roblox.com/share?code={code}&type=Server"

        async with aiohttp.ClientSession(headers=MOBILE_HEADERS) as session:
            # Follow redirects to get final URL
            async with session.get(share_url, allow_redirects=True) as resp:
                final_url = str(resp.url)
                
                if "privateServerLinkCode" not in final_url:
                    raise ValueError("Not a private server link")

                # Create both URLs
                deep_link = create_deep_link(code)
                
                # Build Discord response
                embed = discord.Embed(
                    title="🔗 Roblox Private Server Links",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="🌐 Browser URL",
                    value=f"[Click here]({final_url})",
                    inline=False
                )
                embed.add_field(
                    name="🚀 Direct Launch (Copy-Paste)",
                    value=f"```{deep_link}```",
                    inline=False
                )
                
                # Add browser button
                view = discord.ui.View()
                view.add_item(discord.ui.Button(
                    label="Open in Browser",
                    url=final_url,
                    style=discord.ButtonStyle.url
                ))
                
                await ctx.send(embed=embed, view=view)

    except Exception as e:
        print(f"Error: {e}")
        embed = discord.Embed(
            color=discord.Color.orange(),
            description="⚠️ Failed to process link. It may be expired or invalid."
        )
        await ctx.send(embed=embed)

# Start services
def run():
    # Start Flask in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Start Discord bot
    bot.run(TOKEN)

if __name__ == "__main__":
    run()
