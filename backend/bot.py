import os
from pathlib import Path

import asyncio

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from app.database import SessionLocal
from app.models import ClanSession, Members
from app.services.war_tracking import sync_war_data_once

load_dotenv(Path(__file__).resolve().parent / ".env")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WAR_SYNC_INTERVAL_MINUTES = 5

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
commands_synced = False


def load_warstats_snapshot():
    db = SessionLocal()
    try:
        clan_session = db.query(ClanSession).first()
        members = (
            db.query(Members)
            .order_by(Members.games_played.asc(), Members.name.asc())
            .all()
        )

        return clan_session, members
    finally:
        db.close()


def build_warstats_message():
    clan_session, members = load_warstats_snapshot()

    if clan_session is None:
        return "Es gibt noch keinen gespeicherten Clan-Stand in der Datenbank."

    if not members:
        return "Es gibt noch keine gespeicherten Mitgliederdaten in der Datenbank."

    played_count = sum(1 for member in members if (member.games_played or 0) > 0)
    missing_members = [member for member in members if (member.games_played or 0) == 0]
    total_games = sum(member.games_played or 0 for member in members)

    lines = [
        f"Clan: {clan_session.clan_tag}",
        f"Section Index: {clan_session.section_index}",
        f"Phase: {clan_session.period_type}",
        f"Aktive Mitglieder: {played_count}/{len(members)}",
        f"Gespielte Spiele insgesamt: {total_games}",
    ]

    if missing_members:
        lines.append("")
        lines.append("Noch ohne Spiele:")
        lines.extend(
            f"- {member.name} ({member.member_tag})"
            for member in missing_members[:10]
        )

        if len(missing_members) > 10:
            lines.append(f"... und {len(missing_members) - 10} weitere")

    return "\n".join(lines)


@tasks.loop(minutes=WAR_SYNC_INTERVAL_MINUTES)
async def war_data_sync_loop():
    try:
        result = await asyncio.to_thread(sync_war_data_once)
        print(f"War-Daten synchronisiert: {result}")
    except Exception as exc:
        print(f"Fehler beim periodischen War-Daten-Sync: {exc}")


@war_data_sync_loop.before_loop
async def before_war_data_sync_loop():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    global commands_synced

    if not commands_synced:
        synced = await bot.tree.sync()
        commands_synced = True
        print(f"Bot ist online als {bot.user} - {len(synced)} Slash-Commands synchronisiert.")
    else:
        print(f"Bot ist online als {bot.user}.")

    if not war_data_sync_loop.is_running():
        war_data_sync_loop.start()
        print(f"Periodischer War-Daten-Sync gestartet ({WAR_SYNC_INTERVAL_MINUTES} Minuten).")


@bot.tree.command(name="ping", description="Prüft, ob der Bot erreichbar ist.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong")


@bot.tree.command(name="warstats", description="Zeigt den aktuellen Kriegsstand aus der lokalen Datenbank.")
async def warstats(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    try:
        await asyncio.to_thread(sync_war_data_once)
        message = build_warstats_message()
    except Exception as exc:
        await interaction.followup.send(
            f"War-Daten konnten gerade nicht aktualisiert werden: {exc}"
        )
        return

    await interaction.followup.send(message)


def main():
    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN is not configured in backend/.env")

    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
