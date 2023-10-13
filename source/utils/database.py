from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from datetime import datetime
from typing import Optional

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import *


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

class DBClan(Base):
    __tablename__ = "clans"
    
    server = Column("server", String, primary_key=True)
    clan_id = Column("clan_id", Integer, primary_key=True)
    name = Column("name", String)
    tag = Column("tag", String)
    description = Column("description", String)
    icon = Column("icon", String)
    owner = Column("owner", Integer)
    status = Column("status", Integer) # clan join restriction?

class DBStats(Base):
    __tablename__ = "user_statistics"
    
    user_id = Column('user_id', Integer, primary_key=True)
    server = Column('server', String, primary_key=True)
    mode = Column('mode', SmallInteger, primary_key=True)
    relax = Column('relax', SmallInteger, primary_key=True)
    date = Column('date', Date, primary_key=True)
    ranked_score = Column('ranked_score', BigInteger)
    total_score = Column('total_score', BigInteger)
    play_count = Column('play_count', Integer)
    play_time = Column('play_time', Integer)
    replays_watched = Column('replays_watched', BigInteger)
    total_hits = Column('total_hits', BigInteger)
    level = Column('level', Float)
    accuracy = Column('accuracy', Float)
    pp = Column('pp', Integer)
    global_rank = Column('global_rank', BigInteger)
    country_rank = Column('country_rank', BigInteger)
    global_score_rank = Column('global_score_rank', BigInteger)
    country_score_rank = Column('country_score_rank', BigInteger)
    max_combo = Column('max_combo', SmallInteger)
    first_places = Column('first_places', Integer, default=0)
    clears = Column('clears', Integer, default=0)
    xh_count  = Column('xh_count', Integer, default=0)
    x_count   = Column('x_count', Integer, default=0)
    sh_count  = Column('sh_count', Integer, default=0)
    s_count   = Column('s_count', Integer, default=0)
    a_count   = Column('a_count', Integer, default=0)
    b_count   = Column('b_count', Integer, default=0)
    c_count   = Column('c_count', Integer, default=0)
    d_count   = Column('d_count', Integer, default=0)

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
    mode = Column("mode", SmallInteger)
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
    __tablename__ = "user_scores"
    
    beatmap_id = Column('beatmap_id', Integer, primary_key=True)
    server = Column('server', String, primary_key=True)
    user_id = Column('user_id', Integer, primary_key=True)
    mode = Column('mode', SmallInteger, primary_key=True)
    relax = Column('relax', SmallInteger, primary_key=True)
    score_id = Column('score_id', BigInteger, primary_key=True)
    accuracy = Column('accuracy', Float)
    mods = Column('mods', Integer)
    pp = Column('pp', Float)
    score = Column('score', BigInteger)
    combo = Column('combo', SmallInteger)
    rank = Column('rank', String)
    count_300 = Column('count_300', SmallInteger)
    count_100 = Column('count_100', SmallInteger)
    count_50 = Column('count_50', SmallInteger)
    count_miss = Column('count_miss', SmallInteger)
    completed = Column('completed', SmallInteger)
    date = Column('date', Integer)

# Workaround for akatsuki broken rx playtime since 1984...
class DBAKatsukiPlaytime(Base):
    __tablename__ = "akatsuki_playtime"
    
    user_id = Column('user_id', Integer, primary_key=True)
    mode = Column('mode', SmallInteger, primary_key=True)
    relax = Column('relax', SmallInteger, primary_key=True)
    submitted_plays = Column('submitted_plays', Float)
    unsubmitted_plays = Column('unsubmitted_plays', Float)
    most_played = Column('most_played', Float)
    
class DBTaskStatus(Base):
    __tablename__ = "task_status"
    
    task_name = Column('task_name', String, primary_key=True)
    last_run = Column("last_run", Integer)
    
class DBLiveUser(Base):
    __tablename__ = "live_leaderboard"

    server = Column("server", String, primary_key=True)
    user_id = Column("user_id", Integer, primary_key=True)
    mode = Column("mode", SmallInteger, primary_key=True)
    relax = Column("relax", SmallInteger, primary_key=True)
    global_rank = Column("global_rank", BigInteger)
    country_rank = Column("country_rank", BigInteger)
    ranked_score = Column("ranked_score", BigInteger)
    total_score = Column("total_score", BigInteger)
    play_count = Column("play_count", Integer)
    replays_watched = Column("replays_watched", BigInteger) # copium
    total_hits = Column("total_hits", Integer)
    level = Column("level", Float)
    accuracy = Column("accuracy", Float)
    pp = Column("pp", Integer)

class DBLiveUserScore(Base):
    __tablename__ = "score_leaderboard"

    server = Column("server", String, primary_key=True)
    user_id = Column("user_id", Integer, primary_key=True)
    mode = Column("mode", SmallInteger, primary_key=True)
    relax = Column("relax", SmallInteger, primary_key=True)
    global_rank = Column("global_rank", BigInteger)
    country_rank = Column("country_rank", BigInteger)
    ranked_score = Column("ranked_score", BigInteger)
    total_score = Column("total_score", BigInteger)
    play_count = Column("play_count", Integer)
    replays_watched = Column("replays_watched", BigInteger) # copium
    total_hits = Column("total_hits", Integer)
    level = Column("level", Float)
    accuracy = Column("accuracy", Float)
    pp = Column("pp", Integer)

class DBUserQueue(Base):
    __tablename__ = "user_queue"
    
    server = Column("server", String, primary_key=True)
    user_id = Column("user_id", Integer, primary_key=True)
    mode = Column("mode", SmallInteger, primary_key=True)
    relax = Column("relax", SmallInteger, primary_key=True)
    date = Column('date', Date, primary_key=True)

class DBUserInfo(Base):
    __tablename__ = "user_info"

    server = Column("server", String, primary_key=True)
    user_id = Column("user_id", Integer, primary_key=True)
    mode = Column("mode", SmallInteger, primary_key=True)
    relax = Column("relax", SmallInteger, primary_key=True)
    score_fetched = Column('score_fetched', Date, primary_key=True)

class DBUserFirstPlace(Base):
    __tablename__ = "user_first_places"

    server = Column("server", String, primary_key=True)
    user_id = Column("user_id", Integer, primary_key=True)
    mode = Column("mode", SmallInteger, primary_key=True)
    relax = Column("relax", SmallInteger, primary_key=True)
    date = Column('date', Date, primary_key=True)
    score_id = Column('score_id', BigInteger, primary_key=True)

class DBClanStats(Base):
    __tablename__ = "clan_leaderboard"

    server = Column("server", String, primary_key=True)
    clan_id = Column("clan_id", Integer, primary_key=True)
    mode = Column("mode", SmallInteger, primary_key=True)
    relax = Column("relax", SmallInteger, primary_key=True)
    date = Column('date', Date, primary_key=True)
    global_rank = Column("global_rank", BigInteger)
    global_rank_1s = Column("global_rank_1s", BigInteger)
    ranked_score = Column("ranked_score", BigInteger)
    total_score = Column("total_score", BigInteger)
    play_count = Column("play_count", Integer)
    accuracy = Column("accuracy", Float)
    first_places = Column("first_places", Integer)
    pp = Column("pp", Integer)