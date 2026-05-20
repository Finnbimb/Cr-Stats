import asyncio
import time

import discord
from discord import app_commands
from discord.ext import commands, tasks

from app.database import SessionLocal
from app.models import ClanSession, DiscordPlayerLink, Members
from app.services.clash_royale import fetch_war_creation_date
from app.services.war_tracking import sync_war_data_once

WAR_SYNC_INTERVAL_MINUTES = 5
WAR_REMINDER_CHANNEL_ID = 1492165866589257808
WAR_GAMES_PER_DAY = 4
WAR_REMINDER_HOURS_BEFORE_END = 2


class WarCog(commands.Cog, name="War"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._reminded_for_sections: set[int] = set()

    async def cog_load(self):
        self.war_data_sync_loop.start()

    async def cog_unload(self):
        self.war_data_sync_loop.cancel()

    # --- DB helpers ---

    def _load_warstats_snapshot(self):
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

    def _load_reminder_candidates(self):
        db = SessionLocal()
        try:
            clan_session = db.query(ClanSession).first()
            if clan_session is None:
                return None, []
            members = (
                db.query(Members)
                .filter(Members.games_played_today < WAR_GAMES_PER_DAY)
                .all()
            )
            return clan_session, members
        finally:
            db.close()

    def _load_discord_link(self, player_tag: str):
        db = SessionLocal()
        try:
            return (
                db.query(DiscordPlayerLink)
                .filter(DiscordPlayerLink.player_tag == player_tag)
                .first()
            )
        finally:
            db.close()

    # --- Message builders ---

    @staticmethod
    def _war_day_label(clan_session: ClanSession) -> str:
        return f"Tag {(clan_session.section_index or 0) + 1}"

    def build_warstats_message(self) -> str:
        clan_session, members = self._load_warstats_snapshot()
        if clan_session is None:
            return "Es gibt noch keinen gespeicherten Clan-Stand in der Datenbank."
        if not members:
            return "Es gibt noch keine gespeicherten Mitgliederdaten in der Datenbank."

        missing = [m for m in members if (m.games_played_today or 0) == 0]
        total_games = sum(m.games_played_today or 0 for m in members)
        max_games = len(members) * WAR_GAMES_PER_DAY

        lines = [
            f"Clan: {clan_session.clan_tag}",
            self._war_day_label(clan_session),
            f"Phase: {clan_session.period_type}",
            f"Decks gespielt: {total_games} / {max_games}",
        ]
        if missing:
            lines += ["", f"Bisher ohne Decks: {len(missing)} von {len(members)} Spielern"]
            lines += [f"- {m.name} ({m.member_tag})" for m in missing[:10]]
            if len(missing) > 10:
                lines.append(f"... und {len(missing) - 10} weitere")

        return "\n".join(lines)

    def build_games_played_message(self) -> str:
        clan_session, members = self._load_warstats_snapshot()
        if clan_session is None:
            return "Es gibt noch keinen gespeicherten Clan-Stand in der Datenbank."
        if not members:
            return "Es gibt noch keine gespeicherten Mitgliederdaten in der Datenbank."

        members = sorted(members, key=lambda m: (m.games_played or 0, m.name.lower()), reverse=True)
        lines = [
            f"Gummibärenbande({clan_session.clan_tag}) - {self._war_day_label(clan_session)} - {clan_session.period_type}",
            "Mitglieder nach insgesamt gespielten CW-Spielen:",
        ] + [f"- {m.name} ({m.member_tag}): {m.games_played or 0}" for m in members]
        return "\n".join(lines)

    # --- Reminder ---

    async def send_war_day_reminders(self):
        clan_session, open_members = await asyncio.to_thread(self._load_reminder_candidates)
        if clan_session is None or clan_session.period_type != "warDay":
            return

        section_index = clan_session.section_index
        if section_index in self._reminded_for_sections:
            return

        try:
            creation_date = await asyncio.to_thread(fetch_war_creation_date)
        except Exception as exc:
            print(f"Fehler beim Laden des War-Startdatums: {exc}")
            return

        if creation_date is None:
            return

        day_end = creation_date + (section_index + 1) * 24 * 3600
        now = int(time.time())
        seconds_until_end = day_end - now

        if not (0 < seconds_until_end <= WAR_REMINDER_HOURS_BEFORE_END * 3600):
            return

        mentions: list[tuple] = []
        for member in open_members:
            link = await asyncio.to_thread(self._load_discord_link, member.member_tag)
            if link is None or not link.guild_id:
                continue
            guild = self.bot.get_guild(int(link.guild_id))
            if guild is None:
                continue
            discord_member = guild.get_member(int(link.discord_user_id))
            if discord_member is None:
                continue
            remaining = WAR_GAMES_PER_DAY - (member.games_played_today or 0)
            mentions.append((guild, discord_member.mention, member.name, remaining))

        if not mentions:
            return

        guilds_messages: dict[int, dict] = {}
        for guild, mention, name, remaining in mentions:
            guilds_messages.setdefault(guild.id, {"guild": guild, "lines": []})
            guilds_messages[guild.id]["lines"].append(f"- {mention} ({name}): noch {remaining} Spiel(e)")

        hours_left = round(seconds_until_end / 3600, 1)
        for entry in guilds_messages.values():
            channel = entry["guild"].get_channel(WAR_REMINDER_CHANNEL_ID)
            if channel is None:
                continue
            text = (
                f"**Kriegstag endet in ~{hours_left} Stunden!** Folgende Mitglieder haben noch Spiele offen:\n"
                + "\n".join(entry["lines"])
            )
            try:
                await channel.send(text)
            except (discord.Forbidden, discord.HTTPException) as exc:
                print(f"Fehler beim Senden der War-Erinnerung: {exc}")

        self._reminded_for_sections.add(section_index)
        print(f"War-Erinnerung gesendet für Section {section_index} ({len(mentions)} Spieler).")

    # --- Background task ---

    @tasks.loop(minutes=WAR_SYNC_INTERVAL_MINUTES)
    async def war_data_sync_loop(self):
        try:
            result = await asyncio.to_thread(sync_war_data_once)
            print(f"War-Daten synchronisiert: {result}")
        except Exception as exc:
            print(f"Fehler beim periodischen War-Daten-Sync: {exc}")

        try:
            await self.send_war_day_reminders()
        except Exception as exc:
            print(f"Fehler beim War-Reminder-Check: {exc}")

    @war_data_sync_loop.before_loop
    async def before_war_data_sync_loop(self):
        await self.bot.wait_until_ready()

    # --- Commands ---

    @app_commands.command(name="warstats", description="Zeigt den aktuellen Kriegsstand aus der lokalen Datenbank.")
    async def warstats(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            await asyncio.to_thread(sync_war_data_once)
            message = self.build_warstats_message()
        except Exception as exc:
            await interaction.followup.send(f"War-Daten konnten gerade nicht aktualisiert werden: {exc}")
            return
        await interaction.followup.send(message)

    @app_commands.command(name="war_games_played", description="Zeigt die insgesamt gespielten CW-Spiele")
    async def war_games_played(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            await asyncio.to_thread(sync_war_data_once)
            message = self.build_games_played_message()
        except Exception as exc:
            await interaction.followup.send(f"Die Daten konnten nicht geladen werden: {exc}", ephemeral=True)
            return
        await interaction.followup.send(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(WarCog(bot))
