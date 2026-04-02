import os
import discord
import asyncio
import requests
import json
from datetime import datetime

# ----- Environment Variables -----
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
role_env = os.getenv("ROLE_ID")
ROLE_ID = int(role_env) if role_env else None  # optional role ping

# ----- Supported Platforms -----
ALLOWED_PLATFORMS = [
    "steam",
    "epic games store",
    "ubisoft",
    "origin",
    "ea",
    "gog"
]

# Platform icons (SVGs as clickable links)
PLATFORM_ICONS = {
    "steam": "https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg",
    "epic games store": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Epic_Games_logo.svg",
    "ubisoft": "https://upload.wikimedia.org/wikipedia/commons/0/0e/Ubisoft_Logo_2017.svg",
    "origin": "https://upload.wikimedia.org/wikipedia/commons/0/0b/Origin_Logo.svg",
    "ea": "https://upload.wikimedia.org/wikipedia/commons/7/70/EA_Logo.svg",
    "gog": "https://upload.wikimedia.org/wikipedia/commons/3/3b/GOG.com_logo.svg"
}

# Desktop links
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
    url = "https://www.gamerpower.com/api/giveaways"
    try:
        response = requests.get(url, timeout=10)
        return response.json()
    except Exception as e:
        print("API error:", e)
        return []

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
            platforms = game.get("platforms", "").lower()
            url = game.get("open_giveaway_url")
            image = game.get("image")
            worth = game.get("worth", "N/A")
            end_date = game.get("end_date")

            # Desktop link (first matching platform)
            desktop_link = None
            for p in DESKTOP_LINKS.keys():
                if p in platforms:
                    desktop_link = DESKTOP_LINKS[p]
                    if p == "steam" and "steam" in url:
                        import re
                        match = re.search(r"/app/(\d+)", url)
                        if match:
                            desktop_link = DESKTOP_LINKS["steam"].format(app_id=match.group(1))
                    break

            if gid not in seen and is_allowed(platforms):
                seen.add(gid)
                save_seen()

                embed = discord.Embed(
                    title=title,
                    description=f"**Free on:** {platforms}",
                    color=0x00ff99,
                    url=url
                )
                embed.add_field(name="Original Price", value=worth, inline=True)
                embed.add_field(name="Website", value=f"[Click here]({url})", inline=True)
                if desktop_link:
                    embed.add_field(name="Desktop App", value=f"[Launch]({desktop_link})", inline=True)

                # Footer with end date
                if end_date:
                    try:
                        dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                        embed.set_footer(text=f"Ends on {dt.strftime('%Y-%m-%d %H:%M UTC')}")
                    except:
                        pass

                # Add inline clickable platform icons
                for p, icon_url in PLATFORM_ICONS.items():
                    if p in platforms:
                        embed.add_field(name="\u200b", value=f"[​]({icon_url})", inline=True)

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