from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from datetime import datetime
from typing import Optional

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    SmallInteger,
    ForeignKey,
    BigInteger,
    DateTime,
    Boolean,
    Integer,
    Column,
    String,
    Float
)

Base = declarative_base()

class DBUser(Base):
    __tablename__ = "users"
    
    user_id = Column('user_id', Integer, primary_key=True)
    server = Column('server', String, primary_key=True)
    username = Column('username', String)
    registered_on = Column('registered_on', DateTime)
    latest_activity = Column('latest_activity', DateTime)
    country = Column("country", String)
    clan = Column("clan_id", Integer, default=0)
    followers = Column("followers", Integer)
    
class DBStats(Base):
    __tablename__ = "statistics"
    
    user_id = Column('user_id', Integer, primary_key=True)
    server = Column('server', String, primary_key=True)
    mode = Column('mode', Integer, primary_key=True)
    relax = Column('relax', Integer, primary_key=True)
    ranked_score = Column('ranked_score', Integer)
    total_score = Column('total_score', Integer)
    play_count = Column('play_count', Integer)
    play_time = Column('play_time', Integer)
    replays_watched = Column('replays_watched', Integer)
    total_hits = Column('total_hits', Integer)
    level = Column('level', Float)
    accuracy = Column('accuracy', Float)
    pp = Column('pp', Integer)
    global_rank = Column('global_rank', Integer)
    country_rank = Column('country_rank', Integer)
    max_combo = Column('max_combo', Integer)
    first_places = Column('first_places', Integer, default=0)
    clears = Column('clears', Integer, default=0)

class DBBeatmap(Base):
    __tablename__ = "beatmaps"
    
    beatmap_id = Column("beatmap_id", Integer, primary_key=True, unique=True)
    beatmap_set_id = Column("beatmap_set_id", Integer)
    beatmap_md5 = Column("beatmap_md5", String)
    artist = Column("artist", String)
    title = Column("title", String)
    version = Column("version", String)
    mapper = Column("mapper", String)
    ranked_status = Column("ranked_status", JSONB, default={'bancho': -2, 'akatsuki': -2})
    last_checked = Column('last_checked', DateTime, default=datetime(year=1984, month=1, day=1))
    ar = Column('ar', Float)
    od = Column('od', Float)
    cs = Column('cs', Float)
    length = Column('length', Integer)
    bpm = Column('bpm', Float)
    max_combo = Column('max_combo', Integer)
    circles = Column('circles', Integer)
    sliders = Column('sliders', Integer)
    spinners = Column('spinners', Integer)
    mode = Column("mode", Integer)
    tags = Column("tags", String)
    packs = Column("packs", String)
    stars_nm = Column('stars_nm', Float)
    stars_ez = Column('stars_ez', Float)
    stars_hr = Column('stars_hr', Float)
    stars_dt = Column('stars_dt', Float)
    stars_dtez = Column('stars_dtez', Float)
    stars_dthr = Column('stars_dthr', Float)
    approved_date = Column('approved_date', Integer)

class DBScore(Base):
    __tablename__ = "scores"
    
    beatmap_id = Column('beatmap_id', Integer, primary_key=True)
    mode = Column('mode', Integer, primary_key=True)
    relax = Column('relax', Integer, primary_key=True)
    server = Column('server', String, primary_key=True)
    user_id = Column('user_id', Integer, primary_key=True)
    score_id = Column('score_id', Integer)
    accuracy = Column('accuracy', Float)
    mods = Column('mods', Integer)
    pp = Column('pp', Float)
    score = Column('score', Integer)
    combo = Column('combo', Integer)
    rank = Column('rank', String)
    count_300 = Column('count_300', Integer)
    count_100 = Column('count_100', Integer)
    count_50 = Column('count_50', Integer)
    count_miss = Column('count_miss', Integer)
    date = Column('date', Integer)

# Workaround for akatsuki broken rx playtime since 1984...
class DBAKatsukiPlaytime(Base):
    
    user_id = Column('user_id', Integer, primary_key=True)
    mode = Column('mode', Integer, primary_key=True)
    relax = Column('relax', Integer, primary_key=True)
    submitted_plays = Column('submitted_plays', Float)
    unsubmitted_plays = Column('unsubmitted_plays', Float)
    most_played = Column('most_played', Float)
    
