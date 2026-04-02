import os
import discord
import asyncio
import requests
import json
from datetime import datetime
from io import BytesIO
from PIL import Image

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
role_env = os.getenv("ROLE_ID")
ROLE_ID = int(role_env) if role_env else None  # Only convert to int if set

ALLOWED_PLATFORMS = ["steam", "epic games store", "ubisoft", "origin", "ea", "gog"]

PLATFORM_ICONS = {
    "steam": "https://upload.wikimedia.org/wikipedia/commons/8/83/Steam_icon_logo.svg",
    "epic games store": "https://upload.wikimedia.org/wikipedia/commons/3/3e/Epic_Games_logo.svg",
    "ubisoft": "https://upload.wikimedia.org/wikipedia/commons/0/0e/Ubisoft_Logo_2017.svg",
    "origin": "https://upload.wikimedia.org/wikipedia/commons/0/0b/Origin_Logo.svg",
    "ea": "https://upload.wikimedia.org/wikipedia/commons/7/70/EA_Logo.svg",
    "gog": "https://upload.wikimedia.org/wikipedia/commons/3/3b/GOG.com_logo.svg"
}

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

try:
    with open(SEEN_FILE, "r") as f:
        seen = set(json.load(f))
except:
    seen = set()

def save_seen():
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

def is_allowed(platforms_str):
    return any(p in platforms_str.lower() for p in ALLOWED_PLATFORMS)

def get_free_games():
    try:
        r = requests.get("https://www.gamerpower.com/api/giveaways", timeout=10)
        return r.json()
    except:
        return []

def merge_platform_icons(platforms):
    urls = [PLATFORM_ICONS[p] for p in PLATFORM_ICONS if p in platforms.lower()]
    if not urls:
        return None
    images = []
    for u in urls:
        r = requests.get(u)
        img = Image.open(BytesIO(r.content)).convert("RGBA")
        img = img.resize((32,32))
        images.append(img)
    # create horizontal merge
    total_width = sum(img.width for img in images)
    max_height = max(img.height for img in images)
    new_img = Image.new("RGBA", (total_width, max_height))
    x_offset = 0
    for img in images:
        new_img.paste(img, (x_offset,0), img)
        x_offset += img.width
    b = BytesIO()
    new_img.save(b, format="PNG")
    b.seek(0)
    return b

async def check_free_games():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    role_mention = f"<@&{ROLE_ID}>" if ROLE_ID else ""

    if not channel:
        print(f"Channel {CHANNEL_ID} not found!")
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

            # Desktop link
            desktop_link = None
            for p in DESKTOP_LINKS:
                if p in platforms.lower():
                    desktop_link = DESKTOP_LINKS[p]
                    if p=="steam" and "steam" in url:
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
                if end_date:
                    try:
                        dt = datetime.fromisoformat(end_date.replace("Z","+00:00"))
                        embed.set_footer(text=f"Ends on {dt.strftime('%Y-%m-%d %H:%M UTC')}")
                    except:
                        pass
                # Attach merged platform icons
                icons_img = merge_platform_icons(platforms)
                if icons_img:
                    file = discord.File(fp=icons_img, filename="platforms.png")
                    embed.set_thumbnail(url="attachment://platforms.png")
                    await channel.send(content=role_mention, embed=embed, file=file)
                else:
                    await channel.send(content=role_mention, embed=embed)
        await asyncio.sleep(1800)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(check_free_games())

client.run(DISCORD_TOKEN)