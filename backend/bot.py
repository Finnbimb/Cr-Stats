import os
import json
import subprocess
from pathlib import Path
from discord import app_commands
import time
import asyncio

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from fastapi import HTTPException

from app.database import SessionLocal, init_database
from app.models import ClanSession, DiscordPlayerLink, Members
from app.services.war_tracking import sync_war_data_once
from app.services.clash_royale import (
    fetch_clan_ranking_germany,
    fetch_clanwar_ranking_germany,
    fetch_player_by_tag,
)

load_dotenv(Path(__file__).resolve().parent / ".env")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
WAR_SYNC_INTERVAL_MINUTES = 5
MANAGED_MESSAGES_PATH = Path(__file__).resolve().parent / ".managed_messages.json"
RULES_ROLE_NAME = "Unverifiziert"
CLAN_MEMBER_ROLE_NAME = "Clan Mitglied"
ELDER_ROLE_NAME = "Ältester"
VICE_ROLE_NAME = "Vize"
WELCOME_CHANNEL_ID = 1492165582563311647



intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

commands_synced = False
persistent_views_registered = False


def get_git_revision():
    repo_root = Path(__file__).resolve().parent.parent

    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            text=True,
        ).strip()
    except (subprocess.SubprocessError, OSError):
        return "unknown"


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


def get_war_day_label(clan_session: ClanSession):
    section_index = clan_session.section_index or 0
    return f"Tag {section_index + 1}"


def save_discord_player_link(
    *,
    guild_id: int | None,
    member: discord.Member | discord.User,
    player: dict,
):
    db = SessionLocal()
    discord_user_id = str(member.id)

    try:
        existing_player_link = (
            db.query(DiscordPlayerLink)
            .filter(DiscordPlayerLink.player_tag == player["tag"])
            .first()
        )
        if (
            existing_player_link is not None
            and existing_player_link.discord_user_id != discord_user_id
        ):
            raise ValueError(
                "Dieser Clash Royale Account ist bereits mit einem anderen Discord-Account verknüpft."
            )

        link = (
            db.query(DiscordPlayerLink)
            .filter(DiscordPlayerLink.discord_user_id == discord_user_id)
            .first()
        )
        created = link is None

        if link is None:
            link = DiscordPlayerLink(
                discord_user_id=discord_user_id,
                player_tag=player["tag"],
                registered_at=int(time.time()),
            )
            db.add(link)

        link.guild_id = str(guild_id) if guild_id is not None else None
        link.discord_username = str(member)
        link.discord_display_name = getattr(member, "display_name", None)
        link.player_tag = player["tag"]
        link.player_name = player.get("name")
        link.clan_tag = player.get("clan_tag")
        link.clan_name = player.get("clan_name")
        link.registered_at = int(time.time())

        db.commit()
        db.refresh(link)
        return link, created
    finally:
        db.close()


def build_warstats_message():
    clan_session, members = load_warstats_snapshot()

    if clan_session is None:
        return "Es gibt noch keinen gespeicherten Clan-Stand in der Datenbank."

    if not members:
        return "Es gibt noch keine gespeicherten Mitgliederdaten in der Datenbank."

    played_count = sum(1 for member in members if (member.games_played_today or 0) > 0)
    missing_members = [member for member in members if (member.games_played_today or 0) == 0]
    total_games = sum(member.games_played_today or 0 for member in members)

    lines = [
        f"Clan: {clan_session.clan_tag}",
        f"{get_war_day_label(clan_session)}",
        f"Phase: {clan_session.period_type}",
        f"Aktive Mitglieder: {played_count}/{len(members)}",
        f"Gespielte Spiele heute: {total_games}",
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

    members = sorted(
        members,
        key=lambda member: (member.games_played_today or 0, member.name.lower()),
        reverse=True,
    )

    lines = [
        f"Gummibärenbande({clan_session.clan_tag}) - {get_war_day_label(clan_session)} - {clan_session.period_type}",
        "Mitglieder nach heute gespielten CW-Spielen:",
    ]
    lines.extend(
        f"- {member.name} ({member.member_tag}): {member.games_played_today or 0}"
        for member in members
    )
    return "\n".join(lines)

def build_germany_ranking_message(clan_data: dict):
    
    if not clan_data:
        return "Der Clan ist nicht in der Deutschland-Rangliste gelistet oder es ist ein Fehler aufgetreten."
    
    lines = [
        f"Clan: {clan_data.get('name')} ({clan_data.get('tag')})",
        f"Rang in Deutschland: {clan_data.get('rank')}",
        f"Mitglieder: {clan_data.get('members')}",
    ]
    return "\n".join(lines)


def build_war_points_ranking_message(clan_data: dict):
    if not clan_data:
        return "Der Clan ist nicht in der deutschen Clanwar-Bestenliste gelistet oder es ist ein Fehler aufgetreten."

    members_count = clan_data.get("members")
    if members_count is None:
        members_count = clan_data.get("memberCount")

    lines = [
        f"Clan: {clan_data.get('name')} ({clan_data.get('tag')})",
        f"Rang in Deutschland (Clanwars): {clan_data.get('rank')}, ({clan_data.get('points')} Punkte)",
        f"Mitglieder: {members_count}",
    ]
    return "\n".join(lines)


async def remove_unverified_role(member: discord.Member):
    role = discord.utils.get(member.guild.roles, name=RULES_ROLE_NAME)
    if role is None or role not in member.roles:
        return

    me = member.guild.me
    if me is None:
        me = member.guild.get_member(bot.user.id) if bot.user else None

    if me is None or not me.guild_permissions.manage_roles:
        return

    if role >= me.top_role:
        return

    try:
        await member.remove_roles(role, reason="Clash Royale Registrierung abgeschlossen")
    except (discord.Forbidden, discord.HTTPException):
        return


def get_manageable_role(guild: discord.Guild, role_name: str):
    role = discord.utils.get(guild.roles, name=role_name)
    if role is None:
        return None, f'Die Rolle "{role_name}" existiert auf diesem Server nicht.'

    me = guild.me
    if me is None:
        me = guild.get_member(bot.user.id) if bot.user else None

    if me is None:
        return None, "Ich konnte meine Bot-Rolle im Server nicht prüfen."

    if not me.guild_permissions.manage_roles:
        return None, "Mir fehlt die Berechtigung `Rollen verwalten`."

    if role >= me.top_role:
        return None, (
            f'Die Rolle "{role_name}" liegt über meiner Bot-Rolle. '
            "Ziehe die Bot-Rolle in den Servereinstellungen über diese Rolle."
        )

    return role, None


def member_has_any_role(member: discord.Member, role_names: set[str]):
    return any(role.name in role_names for role in member.roles)


async def grant_clan_member_role(member: discord.Member):
    if member_has_any_role(member, {CLAN_MEMBER_ROLE_NAME, ELDER_ROLE_NAME, VICE_ROLE_NAME}):
        return None

    role, error = get_manageable_role(member.guild, CLAN_MEMBER_ROLE_NAME)
    if error:
        return error

    if role in member.roles:
        return None

    try:
        await member.add_roles(role, reason="Clash Royale Registrierung abgeschlossen")
    except discord.Forbidden:
        return f'Ich darf die Rolle "{CLAN_MEMBER_ROLE_NAME}" aktuell nicht vergeben.'
    except discord.HTTPException as exc:
        return f'Die Rolle "{CLAN_MEMBER_ROLE_NAME}" konnte nicht vergeben werden: {exc}'

    return None

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


class RulesRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label='Akzeptieren ✅',
        style=discord.ButtonStyle.primary,
        custom_id="rules:grant_unverifiziert",
    )
    async def grant_unverifiziert_role(
        self,
        interaction: discord.Interaction,
        _: discord.ui.Button,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "Der Button funktioniert nur auf dem Server.",
                ephemeral=True,
            )
            return

        member = interaction.user
        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                "Ich konnte dein Server-Mitgliedsprofil nicht laden.",
                ephemeral=True,
            )
            return

        if member_has_any_role(
            member,
            {RULES_ROLE_NAME, CLAN_MEMBER_ROLE_NAME, ELDER_ROLE_NAME, VICE_ROLE_NAME},
        ):
            await interaction.response.send_message(
                "Du bist bereits im Registrierungs- oder Mitgliederstatus und kannst diesen Button nicht erneut verwenden.",
                ephemeral=True,
            )
            return

        role = discord.utils.get(interaction.guild.roles, name=RULES_ROLE_NAME)
        if role is None:
            await interaction.response.send_message(
                f'Die Rolle "{RULES_ROLE_NAME}" existiert auf diesem Server nicht.',
                ephemeral=True,
            )
            return

        me = interaction.guild.me
        if me is None:
            me = interaction.guild.get_member(bot.user.id) if bot.user else None

        if me is None:
            await interaction.response.send_message(
                "Ich konnte meine Bot-Rolle im Server nicht prüfen.",
                ephemeral=True,
            )
            return

        if not me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                "Mir fehlt die Berechtigung `Rollen verwalten`.",
                ephemeral=True,
            )
            return

        if role >= me.top_role:
            await interaction.response.send_message(
                f'Die Rolle "{RULES_ROLE_NAME}" liegt über meiner Bot-Rolle.',
                ephemeral=True,
            )
            return

        if role in member.roles:
            await interaction.response.send_message(
                f'Du hast die Rolle "{RULES_ROLE_NAME}" bereits.',
                ephemeral=True,
            )
            return

        try:
            await member.add_roles(role, reason="Regel-Button im Regelchannel")
        except discord.Forbidden:
            await interaction.response.send_message(
                "Ich darf dir diese Rolle aktuell nicht geben.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as exc:
            await interaction.response.send_message(
                f"Die Rolle konnte nicht vergeben werden: {exc}",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f'Die Rolle "{RULES_ROLE_NAME}" wurde dir gegeben. Verifiziere dich schnell unter "registieren" und dann kann es losgehen!',
            ephemeral=True,
        )


async def post_or_update_channel_message(
    channel_id: int,
    *,
    content: str | None = None,
    embed: discord.Embed | None = None,
    view: discord.ui.View | None = None,
    force_new: bool = False,
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

    if force_new and existing_message_id:
        try:
            existing_message = await channel.fetch_message(existing_message_id)
            await existing_message.delete()
        except discord.NotFound:
            pass
        except discord.HTTPException:
            pass

        managed_messages.pop(str(channel_id), None)
        save_managed_messages(managed_messages)
        existing_message_id = None

    if existing_message_id:
        try:
            existing_message = await channel.fetch_message(existing_message_id)
            await existing_message.edit(content=content, embed=embed, view=view)
            refreshed_message = await channel.fetch_message(existing_message.id)
            print(
                f"Managed message updated in channel {channel_id}: "
                f"components={len(refreshed_message.components)}"
            )
            return refreshed_message
        except discord.NotFound:
            managed_messages.pop(str(channel_id), None)
            save_managed_messages(managed_messages)

    # Fallback: if the bot already posted something in this channel before,
    # update the most recent bot-authored message instead of sending a duplicate.
    if not force_new:
        async for existing_message in channel.history(limit=25):
            if existing_message.author.id == bot.user.id:
                await existing_message.edit(content=content, embed=embed, view=view)
                managed_messages[str(channel_id)] = existing_message.id
                save_managed_messages(managed_messages)
                refreshed_message = await channel.fetch_message(existing_message.id)
                print(
                    f"Fallback message updated in channel {channel_id}: "
                    f"components={len(refreshed_message.components)}"
                )
                return refreshed_message

    new_message = await channel.send(content=content, embed=embed, view=view)
    managed_messages[str(channel_id)] = new_message.id
    save_managed_messages(managed_messages)
    refreshed_message = await channel.fetch_message(new_message.id)
    print(
        f"Managed message created in channel {channel_id}: "
        f"components={len(refreshed_message.components)}"
    )
    return refreshed_message


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
    global commands_synced, persistent_views_registered

    git_revision = get_git_revision()

    if not persistent_views_registered:
        bot.add_view(RulesRoleView())
        persistent_views_registered = True

    if not commands_synced:
        synced = await bot.tree.sync()
        commands_synced = True
        print(
            f"Bot ist online als {bot.user} - Version {git_revision} - "
            f"{len(synced)} Slash-Commands synchronisiert."
        )
    else:
        print(f"Bot ist online als {bot.user} - Version {git_revision}.")

    if not war_data_sync_loop.is_running():
        war_data_sync_loop.start()
        print(f"Periodischer War-Daten-Sync gestartet ({WAR_SYNC_INTERVAL_MINUTES} Minuten).")

# COMMAND FÜR PING - PRÜFT, OB DER BOT REAGIERT
@bot.tree.command(name="ping", description="Prüft, ob der Bot erreichbar ist.")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong")


@bot.tree.command(name="bot_version", description="Zeigt die aktuell laufende Bot-Version an.")
async def bot_version(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Aktuelle Bot-Version: `{get_git_revision()}`",
        ephemeral=True,
    )

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
            view=RulesRoleView(),
            force_new=True,
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
    
@bot.tree.command(name="war_games_played", description="Zeigt die heute gespielten CW-Spiele")
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


@bot.tree.command(
    name="war_points_ranking",
    description="Zeigt die deutsche Clanwar-Bestenlistenplatzierung an",
)
async def war_points_ranking(interaction: discord.Interaction):
    await interaction.response.defer(thinking=True)

    try:
        clan_data = await asyncio.to_thread(fetch_clanwar_ranking_germany)
        if not clan_data:
            await interaction.followup.send(
                "Der Clan ist nicht in der deutschen Clanwar-Bestenliste gelistet.",
                ephemeral=True,
            )
            return

        message = build_war_points_ranking_message(clan_data)
    except Exception as exc:
        await interaction.followup.send(
            f"Die Daten konnten nicht geladen werden: {exc}",
            ephemeral=True,
        )
        return

    await interaction.followup.send(message)
    
@app_commands.guild_only()
@app_commands.describe(
    player_tag="Dein Clash Royale Spieler-Tag, z. B. #ABC123"
)
@bot.tree.command(name="register", description="Verknüpft deinen Clash Royale Account.")
async def register(interaction: discord.Interaction, player_tag: str):
    await interaction.response.defer(thinking=True, ephemeral=True)

    try:
        player = await asyncio.to_thread(fetch_player_by_tag, player_tag)
        link, created = await asyncio.to_thread(
            save_discord_player_link,
            guild_id=interaction.guild_id,
            member=interaction.user,
            player=player,
        )
    except HTTPException as exc:
        detail = exc.detail if isinstance(exc.detail, str) else "Die Daten konnten nicht geladen werden."
        await interaction.followup.send(detail, ephemeral=True)
        return
    except ValueError as exc:
        await interaction.followup.send(
            f"Die Daten konnten nicht geladen werden: {exc}",
            ephemeral=True,
        )
        return
    except Exception as exc:
        await interaction.followup.send(
            f"Die Registrierung konnte nicht gespeichert werden: {exc}",
            ephemeral=True,
        )
        return

    role_warning = None
    granted_clan_member_role = False
    if isinstance(interaction.user, discord.Member):
        already_ranked = member_has_any_role(
            interaction.user,
            {CLAN_MEMBER_ROLE_NAME, ELDER_ROLE_NAME, VICE_ROLE_NAME},
        )
        role_warning = await grant_clan_member_role(interaction.user)
        if role_warning is None:
            await remove_unverified_role(interaction.user)
            granted_clan_member_role = not already_ranked

    message = (
        f"Der Spieler {link.player_name} ({link.player_tag}) wurde mit deinem Discord-Account verknüpft."
        if created
        else f"Deine Verknüpfung wurde auf {link.player_name} ({link.player_tag}) aktualisiert."
    )

    if role_warning is None:
        if granted_clan_member_role:
            message = (
                f"{message} Du hast jetzt die Rolle "
                f'"{CLAN_MEMBER_ROLE_NAME}" und Zugriff auf die freigeschalteten Clan-Bereiche.'
            )
        else:
            message = f"{message} Deine bestehenden Server-Rollen bleiben unverändert."
    else:
        message = f"{message} Hinweis zur Rollenvergabe: {role_warning}"

    await interaction.followup.send(message, ephemeral=True)

    

    
@bot.event
async def on_member_join(member: discord.Member):
    print(f"[JOIN] Neuer User: {member} ({member.id}) in Guild {member.guild.name} ({member.guild.id})")

    channel = member.guild.get_channel(WELCOME_CHANNEL_ID)
    print(f"[JOIN] Welcome channel lookup: {WELCOME_CHANNEL_ID} -> {channel}")

    if channel is None:
        print("[JOIN] Welcome channel wurde nicht gefunden.")
        return

    try:
        await channel.send(
            f"👑 Willkommen bei der Gummibärenbande, {member.mention}!\n\n"
            f"📌 Lies die Regeln durch\n"
            f"🔗 Verknüpfe deinen Clash Royale Account mit `/register <dein Spieler-Tag>`\n"
            f"🏆 Viel Erfolg auf der Ladder!"
        )
        print("[JOIN] Willkommensnachricht erfolgreich gesendet.")
    except Exception as exc:
        print(f"[JOIN] Fehler beim Senden der Willkommensnachricht: {exc}")


def main():
    if not DISCORD_BOT_TOKEN:
        raise RuntimeError("DISCORD_BOT_TOKEN is not configured in backend/.env")

    init_database()
    bot.run(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    main()
