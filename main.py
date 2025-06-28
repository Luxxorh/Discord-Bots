import discord
from discord.ext import commands
from flask import Flask
from threading import Thread
import os
import aiohttp
import re
from urllib.parse import quote
import json

# Initialize Flask for 24/7 uptime
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Bot Online | Use !dslink"

# Get token from GitHub Secrets or .env (for local testing)
TOKEN = os.getenv('DISCORD_TOKEN') or os.getenv('TOKEN')
if not TOKEN:
    raise RuntimeError("No token found in environment variables!")

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Constants
SHARE_LINK_RE = re.compile(
    r"https?://(?:www\.)?roblox\.com/share\?code=([0-9a-f]{32})&type=Server"
)
MOBILE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
}

@bot.event
async def on_ready():
    print(f"✅ Bot logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game(name="!dslink"))

def create_deep_link(code: str):
    """Generate Roblox deep link"""
    return f"roblox://navigation/share_links?code={code}&type=Server"

@bot.command(name="dslink", help="Convert Roblox share link to private server URL")
async def dslink(ctx, link: str):
    try:
        match = SHARE_LINK_RE.fullmatch(link.strip())
        if not match:
            embed = discord.Embed(
                color=discord.Color.red(),
                description="❌ **Invalid link!**\nFormat: `https://www.roblox.com/share?code=ABC123...&type=Server`"
            )
            return await ctx.send(embed=embed)

        code = match.group(1)
        share_url = f"https://www.roblox.com/share?code={code}&type=Server"

        async with aiohttp.ClientSession(headers=MOBILE_HEADERS) as session:
            async with session.get(share_url, allow_redirects=True) as resp:
                final_url = str(resp.url)
                
                if "privateServerLinkCode" not in final_url:
                    raise ValueError("Not a private server link")

                embed = discord.Embed(
                    title="🔗 Roblox Private Server",
                    color=discord.Color.green()
                )
                embed.add_field(
                    name="🌐 Browser Link",
                    value=f"[Click Here]({final_url})",
                    inline=False
                )
                embed.add_field(
                    name="🚀 App Deep Link",
                    value=f"```{create_deep_link(code)}```\n*(Copy-paste into browser)*",
                    inline=False
                )
                
                view = discord.ui.View()
                view.add_item(discord.ui.Button(
                    label="Open in Browser",
                    url=final_url,
                    style=discord.ButtonStyle.url
                ))
                
                await ctx.send(embed=embed, view=view)

    except Exception as e:
        print(f"Error: {e}")
        await ctx.send(embed=discord.Embed(
            color=discord.Color.orange(),
            description="⚠️ Failed to process link (expired/invalid)"
        ))

def run():
    # Start Flask server
    Thread(target=lambda: app.run(host='0.0.0.0', port=10000)).start()
    # Start Discord bot
    bot.run(TOKEN)

if __name__ == "__main__":
    run()
