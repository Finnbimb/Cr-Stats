import asyncio
import os
from pathlib import Path

import discord
from discord.ext import commands
from dotenv import load_dotenv

from app.database import init_database

load_dotenv(Path(__file__).resolve().parent / ".env")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

EXTENSIONS = [
    "cogs.registration",  # first: registers persistent views
    "cogs.war",
    "cogs.ranking",
    "cogs.admin",
    "cogs.events",
]

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

commands_synced = False


@bot.event
async def on_ready():
    global commands_synced
    if not commands_synced:
        synced = await bot.tree.sync()
        commands_synced = True
        print(f"Bot ist online als {bot.user} - {len(synced)} Slash-Commands synchronisiert.")
    else:
        print(f"Bot ist online als {bot.user}.")


async def main():
    async with bot:
        for ext in EXTENSIONS:
            await bot.load_extension(ext)
        await bot.start(DISCORD_BOT_TOKEN)


def run():
    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN is not configured in backend/.env")
    init_database()
    asyncio.run(main())


if __name__ == "__main__":
    run()
