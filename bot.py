import os
import discord
import asyncio
import requests
import json
from datetime import datetime
import re

# ----- Environment Variables -----
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
role_env = os.getenv("ROLE_ID")
ROLE_ID = int(role_env) if role_env else None  # optional role ping

# ----- Supported Platforms -----
ALLOWED_PLATFORMS = ["steam", "epic games store", "ubisoft", "origin", "ea", "gog"]

# Desktop links templates
DESKTOP_LINKS = {
    "steam": "steam://store/{app_id}",
    "epic games store": "com.epicgames.launcher://store/",
    "ubisoft": "uplay://open/",
    "origin": "origin://store/",
    "ea": "origin://store/",
    "gog": "gog://open/"
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)
SEEN_FILE = "seen_games.json"

# Load seen giveaways
try:
    with open(SEEN_FILE, "r") as f:
        seen = set(json.load(f))
except:
    seen = set()

def save_seen():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def is_allowed(platforms_str):
    lowerp = platforms_str.lower()
    return any(p in lowerp for p in ALLOWED_PLATFORMS)

def get_free_games():
    try:
        response = requests.get("https://www.gamerpower.com/api/giveaways", timeout=10)
        return response.json()
    except Exception as e:
        print("API error:", e)
        return []

# Function to generate desktop link
def generate_desktop_link(platform, url):
    platform = platform.lower()
    if platform == "steam" and "steam" in url:
        match = re.search(r"/app/(\d+)", url)
        if match:
            return DESKTOP_LINKS["steam"].format(app_id=match.group(1))
    elif platform in DESKTOP_LINKS:
        return DESKTOP_LINKS[platform]
    return None

async def check_free_games():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    role_mention = f"<@&{ROLE_ID}>" if ROLE_ID else ""

    if channel is None:
        print(f"ERROR: Channel ID {CHANNEL_ID} not found!")
        return

    while not client.is_closed():
        giveaways = get_free_games()
        for game in giveaways:
            gid = str(game.get("id"))
            title = game.get("title")
            platforms = game.get("platforms", "")
            url = game.get("open_giveaway_url")
            image = game.get("image")
            worth = game.get("worth", "N/A")
            end_date = game.get("end_date")

            if gid in seen or not is_allowed(platforms):
                continue
            seen.add(gid)
            save_seen()

            # Generate desktop links for all platforms present
            platform_list = [p.strip() for p in platforms.split(",")]
            desktop_links_text = ""
            for p in platform_list:
                link = generate_desktop_link(p, url)
                if link:
                    desktop_links_text += f"[{p} Desktop]({link})  "

            # Create embed
            embed = discord.Embed(
                title=title,
                description=f"**Platforms:** {', '.join(platform_list)}",
                color=0x00ff99,
                url=url
            )
            embed.add_field(name="Original Price", value=worth, inline=True)
            embed.add_field(name="Website", value=f"[Click here]({url})", inline=True)
            if desktop_links_text:
                embed.add_field(name="Desktop App Links", value=desktop_links_text, inline=False)

            # Footer with end date
            if end_date:
                try:
                    dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                    embed.set_footer(text=f"Ends on {dt.strftime('%Y-%m-%d %H:%M UTC')}")
                except:
                    pass

            # Main cover image
            if image:
                embed.set_image(url=image)

            await channel.send(content=role_mention, embed=embed)

        await asyncio.sleep(1800)  # 30 min interval

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(check_free_games())

client.run(DISCORD_TOKEN)