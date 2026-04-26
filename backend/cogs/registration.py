import asyncio
import time

import discord
from discord import app_commands
from discord.ext import commands
from fastapi import HTTPException

from app.database import SessionLocal
from app.models import DiscordPlayerLink
from app.services.clash_royale import fetch_player_by_tag

RULES_ROLE_NAME = "Unverifiziert"
CLAN_MEMBER_ROLE_NAME = "Clan Mitglied"
ELDER_ROLE_NAME = "Ältester"
VICE_ROLE_NAME = "Vize"


def member_has_any_role(member: discord.Member, role_names: set[str]) -> bool:
    return any(role.name in role_names for role in member.roles)


class RulesRoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Akzeptieren ✅",
        style=discord.ButtonStyle.primary,
        custom_id="rules:grant_unverifiziert",
    )
    async def grant_unverifiziert_role(self, interaction: discord.Interaction, _: discord.ui.Button):
        if interaction.guild is None:
            await interaction.response.send_message("Der Button funktioniert nur auf dem Server.", ephemeral=True)
            return

        member = interaction.user
        if not isinstance(member, discord.Member):
            await interaction.response.send_message("Ich konnte dein Server-Mitgliedsprofil nicht laden.", ephemeral=True)
            return

        if member_has_any_role(member, {RULES_ROLE_NAME, CLAN_MEMBER_ROLE_NAME, ELDER_ROLE_NAME, VICE_ROLE_NAME}):
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
            await interaction.response.send_message("Ich konnte meine Bot-Rolle im Server nicht prüfen.", ephemeral=True)
            return

        if not me.guild_permissions.manage_roles:
            await interaction.response.send_message("Mir fehlt die Berechtigung `Rollen verwalten`.", ephemeral=True)
            return

        if role >= me.top_role:
            await interaction.response.send_message(
                f'Die Rolle "{RULES_ROLE_NAME}" liegt über meiner Bot-Rolle.',
                ephemeral=True,
            )
            return

        if role in member.roles:
            await interaction.response.send_message(f'Du hast die Rolle "{RULES_ROLE_NAME}" bereits.', ephemeral=True)
            return

        try:
            await member.add_roles(role, reason="Regel-Button im Regelchannel")
        except discord.Forbidden:
            await interaction.response.send_message("Ich darf dir diese Rolle aktuell nicht geben.", ephemeral=True)
            return
        except discord.HTTPException as exc:
            await interaction.response.send_message(f"Die Rolle konnte nicht vergeben werden: {exc}", ephemeral=True)
            return

        await interaction.response.send_message(
            f'Die Rolle "{RULES_ROLE_NAME}" wurde dir gegeben. Verifiziere dich schnell unter "registieren" und dann kann es losgehen!',
            ephemeral=True,
        )


class RegistrationCog(commands.Cog, name="Registration"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(RulesRoleView())

    # --- Helpers ---

    def _save_discord_player_link(self, *, guild_id, member, player: dict):
        db = SessionLocal()
        discord_user_id = str(member.id)
        try:
            existing = (
                db.query(DiscordPlayerLink)
                .filter(DiscordPlayerLink.player_tag == player["tag"])
                .first()
            )
            if existing is not None and existing.discord_user_id != discord_user_id:
                raise ValueError("Dieser Clash Royale Account ist bereits mit einem anderen Discord-Account verknüpft.")

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

    async def _remove_unverified_role(self, member: discord.Member):
        role = discord.utils.get(member.guild.roles, name=RULES_ROLE_NAME)
        if role is None or role not in member.roles:
            return
        me = member.guild.me
        if me is None or not me.guild_permissions.manage_roles or role >= me.top_role:
            return
        try:
            await member.remove_roles(role, reason="Clash Royale Registrierung abgeschlossen")
        except (discord.Forbidden, discord.HTTPException):
            return

    async def _grant_clan_member_role(self, member: discord.Member) -> str | None:
        if member_has_any_role(member, {CLAN_MEMBER_ROLE_NAME, ELDER_ROLE_NAME, VICE_ROLE_NAME}):
            return None

        role = discord.utils.get(member.guild.roles, name=CLAN_MEMBER_ROLE_NAME)
        if role is None:
            return f'Die Rolle "{CLAN_MEMBER_ROLE_NAME}" existiert auf diesem Server nicht.'

        me = member.guild.me
        if me is None:
            return "Ich konnte meine Bot-Rolle im Server nicht prüfen."
        if not me.guild_permissions.manage_roles:
            return "Mir fehlt die Berechtigung `Rollen verwalten`."
        if role >= me.top_role:
            return (
                f'Die Rolle "{CLAN_MEMBER_ROLE_NAME}" liegt über meiner Bot-Rolle. '
                "Ziehe die Bot-Rolle in den Servereinstellungen über diese Rolle."
            )
        if role in member.roles:
            return None

        try:
            await member.add_roles(role, reason="Clash Royale Registrierung abgeschlossen")
        except discord.Forbidden:
            return f'Ich darf die Rolle "{CLAN_MEMBER_ROLE_NAME}" aktuell nicht vergeben.'
        except discord.HTTPException as exc:
            return f'Die Rolle "{CLAN_MEMBER_ROLE_NAME}" konnte nicht vergeben werden: {exc}'

        return None

    # --- Command ---

    @app_commands.guild_only()
    @app_commands.describe(player_tag="Dein Clash Royale Spieler-Tag, z. B. #ABC123")
    @app_commands.command(name="register", description="Verknüpft deinen Clash Royale Account.")
    async def register(self, interaction: discord.Interaction, player_tag: str):
        await interaction.response.defer(thinking=True, ephemeral=True)

        try:
            player = await asyncio.to_thread(fetch_player_by_tag, player_tag)
            link, created = await asyncio.to_thread(
                self._save_discord_player_link,
                guild_id=interaction.guild_id,
                member=interaction.user,
                player=player,
            )
        except HTTPException as exc:
            detail = exc.detail if isinstance(exc.detail, str) else "Die Daten konnten nicht geladen werden."
            await interaction.followup.send(detail, ephemeral=True)
            return
        except ValueError as exc:
            await interaction.followup.send(str(exc), ephemeral=True)
            return
        except Exception as exc:
            await interaction.followup.send(f"Die Registrierung konnte nicht gespeichert werden: {exc}", ephemeral=True)
            return

        role_warning = None
        granted_clan_member_role = False
        if isinstance(interaction.user, discord.Member):
            already_ranked = member_has_any_role(interaction.user, {CLAN_MEMBER_ROLE_NAME, ELDER_ROLE_NAME, VICE_ROLE_NAME})
            role_warning = await self._grant_clan_member_role(interaction.user)
            if role_warning is None:
                await self._remove_unverified_role(interaction.user)
                granted_clan_member_role = not already_ranked

        message = (
            f"Der Spieler {link.player_name} ({link.player_tag}) wurde mit deinem Discord-Account verknüpft."
            if created
            else f"Deine Verknüpfung wurde auf {link.player_name} ({link.player_tag}) aktualisiert."
        )

        if role_warning is None:
            if granted_clan_member_role:
                message = f"{message} Du hast jetzt die Rolle \"{CLAN_MEMBER_ROLE_NAME}\" und Zugriff auf die freigeschalteten Clan-Bereiche."
            else:
                message = f"{message} Deine bestehenden Server-Rollen bleiben unverändert."
        else:
            message = f"{message} Hinweis zur Rollenvergabe: {role_warning}"

        await interaction.followup.send(message, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(RegistrationCog(bot))
