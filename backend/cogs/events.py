import discord
from discord.ext import commands

WELCOME_CHANNEL_ID = 1492165582563311647


class EventsCog(commands.Cog, name="Events"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
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


async def setup(bot: commands.Bot):
    await bot.add_cog(EventsCog(bot))
