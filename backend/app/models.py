from sqlalchemy import Column, Integer, String
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
    

