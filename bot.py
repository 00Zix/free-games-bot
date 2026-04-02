import os
import discord
import asyncio
import requests
import json

# ----- Environment Variables -----
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# ----- Platforms to track -----
ALLOWED_PLATFORMS = [
    "steam",
    "epic games store",
    "ubisoft",
    "origin",
    "ea",
    "gog"
]

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

# Check if any of the user platforms are allowed
def is_allowed(platforms_str):
    lowerp = platforms_str.lower()
    return any(p in lowerp for p in ALLOWED_PLATFORMS)

# Fetch giveaways from the API
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
                embed.add_field(name="Claim Link", value=f"[Click here]({url})", inline=True)
                
                if image:
                    embed.set_image(url=image)

                await channel.send(embed=embed)

        # check again after 30 minutes
        await asyncio.sleep(1800)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(check_free_games())

client.run(DISCORD_TOKEN)