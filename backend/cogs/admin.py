import json
import subprocess
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from cogs.registration import RulesRoleView

MANAGED_MESSAGES_PATH = Path(__file__).resolve().parent.parent / ".managed_messages.json"


def get_git_revision() -> str:
    repo_root = Path(__file__).resolve().parent.parent.parent
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            text=True,
        ).strip()
    except (subprocess.SubprocessError, OSError):
        return "unknown"


def build_rules_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Clan- & Server-Regeln",
        description="Damit alles sauber und entspannt läuft, gelten diese Regeln für alle Mitglieder.",
        color=discord.Color.gold(),
    )
    embed.add_field(name="1. Aktivität ist Pflicht", value="War-Angriffe werden erwartet. Wer dauerhaft nichts macht, fällt auf.", inline=False)
    embed.add_field(name="2. Kein Spam / kein Müll", value="Keine sinnlosen Nachrichten, kein Nerven, kein unnötiges Vollschreiben des Chats.", inline=False)
    embed.add_field(name="3. Respektvoll bleiben", value="Kein toxisches Verhalten, keine Beleidigungen, kein unnötiger Stress.", inline=False)
    embed.add_field(name="4. Discord gehört dazu", value="Wichtige Infos, Rankings und Aktivität laufen hier. Wer im Clan bleiben will, sollte hier mitlesen.", inline=False)
    embed.add_field(name="Wichtig", value="Wer aktiv am Krieg und Chat teilnimmt, wird bevorzugt. Wer dauerhaft inaktiv ist oder stört, kann entfernt werden.", inline=False)
    embed.set_footer(text="CrStats Bot")
    return embed


class AdminCog(commands.Cog, name="Admin"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _load_managed_messages(self) -> dict:
        if not MANAGED_MESSAGES_PATH.exists():
            return {}
        try:
            return json.loads(MANAGED_MESSAGES_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_managed_messages(self, managed_messages: dict):
        MANAGED_MESSAGES_PATH.write_text(json.dumps(managed_messages))

    async def post_or_update_channel_message(
        self,
        channel_id: int,
        *,
        content: str | None = None,
        embed: discord.Embed | None = None,
        view: discord.ui.View | None = None,
        force_new: bool = False,
    ):
        if self.bot.user is None:
            raise RuntimeError("Bot is not ready yet.")

        channel = self.bot.get_channel(channel_id) or await self.bot.fetch_channel(channel_id)
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            raise TypeError("Channel must be a text channel or thread.")

        managed = self._load_managed_messages()
        existing_id = managed.get(str(channel_id))

        if force_new and existing_id:
            try:
                await (await channel.fetch_message(existing_id)).delete()
            except (discord.NotFound, discord.HTTPException):
                pass
            managed.pop(str(channel_id), None)
            self._save_managed_messages(managed)
            existing_id = None

        if existing_id:
            try:
                msg = await channel.fetch_message(existing_id)
                await msg.edit(content=content, embed=embed, view=view)
                refreshed = await channel.fetch_message(msg.id)
                print(f"Managed message updated in channel {channel_id}: components={len(refreshed.components)}")
                return refreshed
            except discord.NotFound:
                managed.pop(str(channel_id), None)
                self._save_managed_messages(managed)

        if not force_new:
            async for msg in channel.history(limit=25):
                if msg.author.id == self.bot.user.id:
                    await msg.edit(content=content, embed=embed, view=view)
                    managed[str(channel_id)] = msg.id
                    self._save_managed_messages(managed)
                    refreshed = await channel.fetch_message(msg.id)
                    print(f"Fallback message updated in channel {channel_id}: components={len(refreshed.components)}")
                    return refreshed

        new_msg = await channel.send(content=content, embed=embed, view=view)
        managed[str(channel_id)] = new_msg.id
        self._save_managed_messages(managed)
        refreshed = await channel.fetch_message(new_msg.id)
        print(f"Managed message created in channel {channel_id}: components={len(refreshed.components)}")
        return refreshed

    # --- Commands ---

    @app_commands.command(name="ping", description="Prüft, ob der Bot erreichbar ist.")
    async def ping(self, interaction: discord.Interaction):
        await interaction.response.send_message("Pong")

    @app_commands.command(name="bot_version", description="Zeigt die aktuell laufende Bot-Version an.")
    async def bot_version(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Aktuelle Bot-Version: `{get_git_revision()}`", ephemeral=True)

    @app_commands.dm_only()
    @app_commands.command(name="publish_message", description="Postet oder aktualisiert eine Bot-Nachricht in einem Zielchannel.")
    async def publish_message(self, interaction: discord.Interaction, channel_id: str, content: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        if interaction.guild is not None:
            await interaction.followup.send("Diesen Command bitte per DM an den Bot benutzen.", ephemeral=True)
            return
        try:
            msg = await self.post_or_update_channel_message(int(channel_id.strip()), content=content)
        except ValueError:
            await interaction.followup.send("Die Channel-ID muss eine Zahl sein.", ephemeral=True)
            return
        except Exception as exc:
            await interaction.followup.send(f"Die Nachricht konnte nicht veröffentlicht werden: {exc}", ephemeral=True)
            return
        await interaction.followup.send(f"Nachricht in <#{msg.channel.id}> veröffentlicht oder aktualisiert.", ephemeral=True)

    @app_commands.dm_only()
    @app_commands.command(name="publish_rules", description="Postet oder aktualisiert die Regeln als formatiertes Embed in einem Zielchannel.")
    async def publish_rules(self, interaction: discord.Interaction, channel_id: str):
        await interaction.response.defer(thinking=True, ephemeral=True)
        try:
            msg = await self.post_or_update_channel_message(
                int(channel_id.strip()),
                embed=build_rules_embed(),
                view=RulesRoleView(),
                force_new=True,
            )
        except ValueError:
            await interaction.followup.send("Die Channel-ID muss eine Zahl sein.", ephemeral=True)
            return
        except Exception as exc:
            await interaction.followup.send(f"Die Regeln konnten nicht veröffentlicht werden: {exc}", ephemeral=True)
            return
        await interaction.followup.send(f"Regeln in <#{msg.channel.id}> veröffentlicht oder aktualisiert.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCog(bot))
