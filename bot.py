import os
import discord
import asyncio
import json
import requests

# ----- Environment Variables -----
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# ----- Supported Platforms -----
PLATFORM_LINKS = {
    "Steam": {"store": "https://store.steampowered.com/", "app": "steam://store/"},
    "Epic Games": {"store": "https://www.epicgames.com/store/en-US/free-games", "app": "com.epicgames.launcher://store/"},
    "Ubisoft": {"store": "https://store.ubi.com/", "app": "uplay://open/"},
    "EA / Origin": {"store": "https://www.origin.com/", "app": "origin://store/"},
    "GOG": {"store": "https://www.gog.com/", "app": "gog://open/"}
}

# ----- Initialize Bot -----
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ----- File to track posted games -----
SEEN_GAMES_FILE = "seen_games.json"

# ----- Load seen games -----
try:
    with open(SEEN_GAMES_FILE, "r") as f:
        seen_games = json.load(f)
except FileNotFoundError:
    seen_games = []

# ----- Helper: Send embed alert -----
async def send_free_game_alert(channel, game_name, platform, price, image_url, store_url):
    embed = discord.Embed(
        title=game_name,
        description=f"Free on {platform}!",
        color=0x00ff99,
        url=store_url
    )
    embed.add_field(name="Price", value=price, inline=True)
    embed.add_field(name="Open in App", value=f"[Launch]({PLATFORM_LINKS[platform]['app']})", inline=True)
    embed.set_image(url=image_url)
    
    await channel.send(embed=embed)

# ----- Main: Check for free games -----
async def check_free_games():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if channel is None:
        print(f"ERROR: Channel with ID {CHANNEL_ID} not found!")
        return

    while not client.is_closed():
        # --- EXAMPLE MOCK DATA FOR TESTING ---
        # Replace this with actual API calls / scraping for each platform
        free_games = [
            {
                "name": "Test Game",
                "platform": "Steam",
                "price": "$0.00",
                "image_url": "https://via.placeholder.com/512",
                "store_url": "https://store.steampowered.com/app/123456/Test_Game/"
            }
        ]
        # -------------------------------------

        for game in free_games:
            if game["name"] not in seen_games:
                await send_free_game_alert(
                    channel,
                    game_name=game["name"],
                    platform=game["platform"],
                    price=game["price"],
                    image_url=game["image_url"],
                    store_url=game["store_url"]
                )
                seen_games.append(game["name"])

        # Save seen games
        with open(SEEN_GAMES_FILE, "w") as f:
            json.dump(seen_games, f)

        # Check every 30 minutes
        await asyncio.sleep(60)

# ----- Bot Events -----
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if channel is not None:
        await channel.send("✅ FreeGamesBot is online and ready!")
    else:
        print(f"ERROR: Channel with ID {CHANNEL_ID} not found!")
    client.loop.create_task(check_free_games())

# ----- Run Bot -----
client.run(DISCORD_TOKEN)