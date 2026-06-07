from sqlalchemy import Column, Integer, String, UniqueConstraint
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    clan_tag = Column(String, nullable=True)
    location_id = Column(Integer, nullable=True)
    location = Column(String, nullable=True)
    clan_ranking = Column(Integer, nullable=True)
    
class ClanSession(Base):
    __tablename__ = "clan_session"

    id = Column(Integer, primary_key=True, index=True)
    clan_tag = Column(String, unique=True, index=True, nullable=False)
    section_index = Column(Integer, nullable=True)
    period_type = Column(String, nullable=True)
    updated_at = Column(Integer, nullable=True)
    
class Members(Base):
    __tablename__ = "members"

    id = Column(Integer, primary_key=True, index=True)
    clan_tag = Column(String, index=True, nullable=False)
    member_tag = Column(String, nullable=False)
    name = Column(String, nullable=False)
    games_played = Column(Integer, nullable=True)
    games_played_today = Column(Integer, nullable=True)
    boat_attacks = Column(Integer, nullable=True)
    updated_at = Column(Integer, nullable=True)
    
class ExcusedPlayer(Base):
    __tablename__ = "excused_players"

    id = Column(Integer, primary_key=True, index=True)
    player_tag = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    clan_tag = Column(String, nullable=True)
    reason = Column(String, nullable=True)
    excused_at = Column(Integer, nullable=False)
    excused_until = Column(Integer, nullable=True)


class ClanRankingSnapshot(Base):
    __tablename__ = "clan_ranking_snapshots"
    __table_args__ = (UniqueConstraint("clan_tag", "snapshot_date"),)

    id = Column(Integer, primary_key=True, index=True)
    clan_tag = Column(String, index=True, nullable=False)
    location_id = Column(Integer, nullable=False)
    location_name = Column(String, nullable=True)
    snapshot_date = Column(String, index=True, nullable=False)  # "YYYY-MM-DD"
    trophy_rank = Column(Integer, nullable=True)
    war_rank = Column(Integer, nullable=True)
    clan_score = Column(Integer, nullable=True)
    clan_war_trophies = Column(Integer, nullable=True)
    captured_at = Column(Integer, nullable=False)


class DiscordPlayerLink(Base):
    __tablename__ = "discord_player_links"

    id = Column(Integer, primary_key=True, index=True)
    guild_id = Column(String, index=True, nullable=True)
    discord_user_id = Column(String, unique=True, index=True, nullable=False)
    discord_username = Column(String, nullable=True)
    discord_display_name = Column(String, nullable=True)
    player_tag = Column(String, unique=True, index=True, nullable=False)
    player_name = Column(String, nullable=True)
    clan_tag = Column(String, nullable=True)
    clan_name = Column(String, nullable=True)
    registered_at = Column(Integer, nullable=False)
    
    
