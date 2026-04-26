import asyncio

import discord
from discord import app_commands
from discord.ext import commands

from app.services.clash_royale import (
    fetch_clan_ranking_germany,
    fetch_clanwar_ranking_germany,
)


class RankingCog(commands.Cog, name="Ranking"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @staticmethod
    def _build_germany_ranking_message(clan_data: dict) -> str:
        if not clan_data:
            return "Der Clan ist nicht in der Deutschland-Rangliste gelistet oder es ist ein Fehler aufgetreten."
        return "\n".join([
            f"Clan: {clan_data.get('name')} ({clan_data.get('tag')})",
            f"Rang in Deutschland: {clan_data.get('rank')}",
            f"Mitglieder: {clan_data.get('members')}",
        ])

    @staticmethod
    def _build_war_points_ranking_message(clan_data: dict) -> str:
        if not clan_data:
            return "Der Clan ist nicht in der deutschen Clanwar-Bestenliste gelistet oder es ist ein Fehler aufgetreten."
        members_count = clan_data.get("members") or clan_data.get("memberCount")
        return "\n".join([
            f"Clan: {clan_data.get('name')} ({clan_data.get('tag')})",
            f"Rang in Deutschland (Clanwars): {clan_data.get('rank')}, ({clan_data.get('clanScore')} Punkte)",
            f"Mitglieder: {members_count}",
        ])

    @app_commands.command(name="germany_ranking", description="Zeigt die aktuelle Deutschland-Rangliste an")
    async def germany_ranking(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            clan_data = await asyncio.to_thread(fetch_clan_ranking_germany)
            if not clan_data:
                await interaction.followup.send(
                    "Der Clan ist nicht in der Deutschland-Rangliste gelistet oder es ist ein Fehler aufgetreten.",
                    ephemeral=True,
                )
                return
            await interaction.followup.send(self._build_germany_ranking_message(clan_data))
        except Exception as exc:
            await interaction.followup.send(f"Die Daten konnten nicht geladen werden: {exc}", ephemeral=True)

    @app_commands.command(name="war_points_ranking", description="Zeigt die deutsche Clanwar-Bestenlistenplatzierung an")
    async def war_points_ranking(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        try:
            clan_data = await asyncio.to_thread(fetch_clanwar_ranking_germany)
            if not clan_data:
                await interaction.followup.send(
                    "Der Clan ist nicht in der deutschen Clanwar-Bestenliste gelistet.",
                    ephemeral=True,
                )
                return
            await interaction.followup.send(self._build_war_points_ranking_message(clan_data))
        except Exception as exc:
            await interaction.followup.send(f"Die Daten konnten nicht geladen werden: {exc}", ephemeral=True)



async def setup(bot: commands.Bot):
    await bot.add_cog(RankingCog(bot))
