import os
import json
from pathlib import Path
from discord import app_commands
import time
import asyncio

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from app.database import SessionLocal
from app.models import ClanSession, Members
from app.services.war_tracking import sync_war_data_once
from app.services.clash_royale import fetch_clan_ranking_germany

load_dotenv(Path(__file__).resolve().parent / ".env")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WAR_SYNC_INTERVAL_MINUTES = 5
MANAGED_MESSAGES_PATH = Path(__file__).resolve().parent / ".managed_messages.json"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
commands_synced = False


def load_managed_messages():
    if not MANAGED_MESSAGES_PATH.exists():
        return {}

    try:
        return json.loads(MANAGED_MESSAGES_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return {}


def save_managed_messages(managed_messages: dict):
    MANAGED_MESSAGES_PATH.write_text(json.dumps(managed_messages))


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
        # clan session session index + 1 
        f"Woche: {clan_session.section_index + 1}",
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

def build_games_played_message():
    clan_session, members = load_warstats_snapshot()
    
    if clan_session is None:
        return "Es gibt noch keinen gespeicherten Clan-Stand in der Datenbank."

    if not members:
        return "Es gibt noch keine gespeicherten Mitgliederdaten in der Datenbank."

    lines = [
        f"Gummibärenbande({clan_session.clan_tag}) - Woche {clan_session.section_index + 1} - {clan_session.period_type}",
        "Mitglieder nach gespielten CW-Spielen:",
    ]
    lines.extend(
        f"- {member.name} ({member.member_tag}): {member.games_played or 0}"
        for member in members
    )
    return "\n".join(lines)

def build_germany_ranking_message(clan_data: dict):
    clan_data = fetch_clan_ranking_germany()
    
    if not clan_data:
        return "Der Clan ist nicht in der Deutschland-Rangliste gelistet oder es ist ein Fehler aufgetreten."
    
    lines = [
        f"Clan: {clan_data.get('name')} ({clan_data.get('tag')})",
        f"Rang in Deutschland: {clan_data.get('rank')}",
        f"Mitglieder: {clan_data.get('members')}",
    ]
    return "\n".join(lines)

def build_rules_embed():
    embed = discord.Embed(
        title="Clan- & Server-Regeln",
        description="Damit alles sauber und entspannt läuft, gelten diese Regeln für alle Mitglieder.",
        color=discord.Color.gold(),
    )
    embed.add_field(
        name="1. Aktivität ist Pflicht",
        value="War-Angriffe werden erwartet. Wer dauerhaft nichts macht, fällt auf.",
        inline=False,
    )
    embed.add_field(
        name="2. Kein Spam / kein Müll",
        value="Keine sinnlosen Nachrichten, kein Nerven, kein unnötiges Vollschreiben des Chats.",
        inline=False,
    )
    embed.add_field(
        name="3. Respektvoll bleiben",
        value="Kein toxisches Verhalten, keine Beleidigungen, kein unnötiger Stress.",
        inline=False,
    )
    embed.add_field(
        name="4. Discord gehört dazu",
        value="Wichtige Infos, Rankings und Aktivität laufen hier. Wer im Clan bleiben will, sollte hier mitlesen.",
        inline=False,
    )
    embed.add_field(
        name="Wichtig",
        value="Wer aktiv am Krieg und Chat teilnimmt, wird bevorzugt. Wer dauerhaft inaktiv ist oder stört, kann entfernt werden.",
        inline=False,
    )
    embed.set_footer(text="CrStats Bot")
    return embed


async def post_or_update_channel_message(
    channel_id: int,
    *,
    content: str | None = None,
    embed: discord.Embed | None = None,
):
    if bot.user is None:
        raise RuntimeError("Bot is not ready yet.")

    channel = bot.get_channel(channel_id)
    if channel is None:
        channel = await bot.fetch_channel(channel_id)

    if not isinstance(channel, (discord.TextChannel, discord.Thread)):
        raise TypeError("Channel must be a text channel or thread.")

    managed_messages = load_managed_messages()
    existing_message_id = managed_messages.get(str(channel_id))

    if existing_message_id:
        try:
            existing_message = await channel.fetch_message(existing_message_id)
            await existing_message.edit(content=content, embed=embed)
            return existing_message
        except discord.NotFound:
            managed_messages.pop(str(channel_id), None)
            save_managed_messages(managed_messages)

    # Fallback: if the bot already posted something in this channel before,
    # update the most recent bot-authored message instead of sending a duplicate.
    async for existing_message in channel.history(limit=25):
        if existing_message.author.id == bot.user.id:
            await existing_message.edit(content=content, embed=embed)
            managed_messages[str(channel_id)] = existing_message.id
            save_managed_messages(managed_messages)
            return existing_message

    new_message = await channel.send(content=content, embed=embed)
    managed_messages[str(channel_id)] = new_message.id
    save_managed_messages(managed_messages)
    return new_message


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

# COMMAND FÜR PING - PRÜFT, OB DER BOT REAGIERT
@bot.tree.command(name="ping", description="Prüft, ob der Bot erreichbar ist.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong")

# COMMAND FÜR WARSTATS - ZEIGT AKTUELLEN KRIEGSSTAND AUS DER DATENBANK
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

# COMMAND FÜR BOT DM - KANN NACHRICHT POSTEN (DM ONLY)
@app_commands.dm_only()
@bot.tree.command(
    name="publish_message",
    description="Postet oder aktualisiert eine Bot-Nachricht in einem Zielchannel."
)
async def publish_message(
    interaction: discord.Interaction,
    channel_id: str,
    content: str,
):
    await interaction.response.defer(thinking=True, ephemeral=True)

    if interaction.guild is not None:
        await interaction.followup.send(
            "Diesen Command bitte per DM an den Bot benutzen.",
            ephemeral=True,
        )
        return

    try:
        target_channel_id = int(channel_id.strip())
        target_message = await post_or_update_channel_message(
            target_channel_id,
            content=content,
        )
    except ValueError:
        await interaction.followup.send(
            "Die Channel-ID muss eine Zahl sein.",
            ephemeral=True,
        )
        return
    except Exception as exc:
        await interaction.followup.send(
            f"Die Nachricht konnte nicht veröffentlicht werden: {exc}",
            ephemeral=True,
        )
        return

    await interaction.followup.send(
        f"Nachricht in <#{target_message.channel.id}> veröffentlicht oder aktualisiert.",
        ephemeral=True,
    )

# COMMAND FÜR REGELN - POSTET EIN FESTES EMBED MIT DEN REGELN IN EINEN CHANNEL (DM ONLY)
@app_commands.dm_only()
@bot.tree.command(
    name="publish_rules",
    description="Postet oder aktualisiert die Regeln als formatiertes Embed in einem Zielchannel."
)
async def publish_rules(
    interaction: discord.Interaction,
    channel_id: str,
):
    await interaction.response.defer(thinking=True, ephemeral=True)

    try:
        target_channel_id = int(channel_id.strip())
        target_message = await post_or_update_channel_message(
            target_channel_id,
            embed=build_rules_embed(),
        )
    except ValueError:
        await interaction.followup.send(
            "Die Channel-ID muss eine Zahl sein.",
            ephemeral=True,
        )
        return
    except Exception as exc:
        await interaction.followup.send(
            f"Die Regeln konnten nicht veröffentlicht werden: {exc}",
            ephemeral=True,
        )
        return

    await interaction.followup.send(
        f"Regeln in <#{target_message.channel.id}> veröffentlicht oder aktualisiert.",
        ephemeral=True,
    )
    
@bot.tree.command(name="war_games_played", description="Zeigt die Anzahl gespielter CW-Spiele")
async def war_games_played(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    try:
        await asyncio.to_thread(sync_war_data_once)
        message = build_games_played_message()
    except Exception as exc:
        await interaction.followup.send(
            f"Die Daten konnten nicht geladen werden: {exc}",
            ephemeral=True,
        )
        return

    await interaction.followup.send(message)
    
@bot.tree.command(name = "germany_ranking", description="Zeigt die aktuelle Deutschland-Rangliste an")
async def germany_ranking(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    try:
        clan_data = await asyncio.to_thread(fetch_clan_ranking_germany)
        if not clan_data:
            await interaction.followup.send(
                "Der Clan ist nicht in der Deutschland-Rangliste gelistet oder es ist ein Fehler aufgetreten.",
                ephemeral=True,
            )
            return

        message = build_germany_ranking_message(clan_data)
    except Exception as exc:
        await interaction.followup.send(
            f"Die Daten konnten nicht geladen werden: {exc}",
            ephemeral=True,
        )
        return

    await interaction.followup.send(message)

def main():
    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN is not configured in backend/.env")

    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
