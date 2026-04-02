import discord
import requests
import asyncio
import json
import os

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

ALLOWED_PLATFORMS = ["steam", "epic games store", "ubisoft", "gog", "origin", "ea"]

intents = discord.Intents.default()
client = discord.Client(intents=intents)

SEEN_FILE = "seen_games.json"

def load_seen():
    try:
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    except:
        return set()

def save_seen(seen):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

seen_games = load_seen()

def is_allowed(platforms):
    return any(p in platforms.lower() for p in ALLOWED_PLATFORMS)

def get_free_games():
    return requests.get("https://www.gamerpower.com/api/giveaways").json()

async def check_games():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    while not client.is_closed():
        try:
            games = get_free_games()

            for game in games:
                game_id = str(game["id"])

                if game_id not in seen_games and is_allowed(game["platforms"]):
                    seen_games.add(game_id)
                    save_seen(seen_games)

                    embed = discord.Embed(
                        title=game["title"],
                        description=game["description"],
                        color=0x00ff99,
                        url=game["open_giveaway_url"]
                    )

                    embed.add_field(name="Platform", value=game["platforms"], inline=False)
                    embed.add_field(name="Worth", value=game["worth"], inline=True)

                    embed.set_image(url=game["image"])

                    await channel.send(embed=embed)

        except Exception as e:
            print("Error:", e)

        await asyncio.sleep(60)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    client.loop.create_task(check_games())

client.run(TOKEN)