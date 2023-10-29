
from utils.api.servers import servers
from api.filter import build_query
import utils.postgres as postgres
from utils.database import *

from fastapi import FastAPI
import datetime
import uvicorn

sort_desc = desc
sort_asc = asc

app = FastAPI()

class TypeEnum(str, Enum):
    pp = "pp"
    score = "score"
    first_places = "1s"
    clears = "clears"

class FirstPlacesEnum(str, Enum):
    all = "all"
    new = "new"
    lost = "lost"

class ScoreSortEnum(str, Enum):
    beatmap_id = "beatmap_id"
    score_id = "score_id"
    accuracy = "accuracy"
    mods = "mods"
    pp = "pp"
    score = "score"
    combo = "combo"
    rank = "rank"
    date = "date"

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/leaderboard/user")
async def get_user_leaderboard(server="akatsuki", mode:int=0, relax:int=0, page:int=1, length:int=100, type: str = TypeEnum.pp):
    length = min(100, length)
    orders = {'pp': 'global_rank', 'score': 'global_score_rank'}
    order = orders['pp']
    if type in orders:
        order = orders[type]
    users = []
    with postgres.instance.managed_session() as session:
        if order == 'global_rank' or order == 'global_score_rank':
            model = DBLiveUser if order == 'global_rank' else DBLiveUserScore
            for stats in session.query(model).filter(model.server == server, model.mode == mode, 
                                                     model.relax == relax).order_by(
                                                         model.global_rank).offset((page-1)*length).limit(length).all():
                users.append(stats)
    return users

@app.get("/leaderboard/user_extra")
async def get_user_statistics(server="akatsuki", date=str(datetime.datetime.now().date()), mode:int=0, relax:int=0, page:int=1, length:int=100, type: str = TypeEnum.clears):
    length = min(100, length)
    orders = {
        'pp': 'global_rank', 
        'score': 'global_score_rank', 
        'total_score': 'total_score DESC', 
        'clears': 'clears DESC', 
        '1s': 'first_places DESC', 
        'xh_count': 'xh_count DESC', 
        'x_count': 'x_count DESC', 
        'sh_count': 'sh_count DESC', 
        's_count': 's_count DESC',
        'a_count': 'a_count DESC',
        'b_count': 'b_count DESC',
        'c_count': 'c_count DESC',
        'd_count': 'd_count DESC',
    }
    order = orders['pp']
    if type in orders:
        order = orders[type]
    users = []
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    with postgres.instance.managed_session() as session:
        for stats in session.query(DBStats).filter(DBStats.server == server, DBStats.mode == mode,
                                                   DBStats.relax == relax, DBStats.date == date).order_by(
                                                       text(order)).offset((page-1)*length).limit(length).all():
            users.append(stats)
    return users

@app.get("/leaderboard/clan")
async def get_clan_leaderboard(server="akatsuki", mode:int=0, relax:int=0, date=str(datetime.datetime.now().date()), page:int=1, length:int=100, type: str = TypeEnum.pp):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    length = min(100, length)
    users = []
    with postgres.instance.managed_session() as session:
        orders = {'pp': 'global_rank', '1s': 'global_rank_1s', 'score': 'ranked_score DESC', 'total_score': 'total_score DESC', 'play_count': 'play_count DESC'}
        order = orders['pp']
        if type in orders:
            order = orders[type]
        for stats in session.query(DBClanStats).filter(DBClanStats.server == server, DBClanStats.mode == mode, 
                                                     DBClanStats.relax == relax, DBClanStats.date == date).order_by(
                                                         text(order)).offset((page-1)*length).limit(length).all():
            users.append(stats)
    return users


@app.get("/user/stats")
async def get_user(user_id:int, server="akatsuki", mode:int=0, relax:int=0,date=str(datetime.datetime.now().date())):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    with postgres.instance.managed_session() as session:
        return session.get(DBStats, (user_id, server, mode, relax, date))

@app.get("/user/first_places")
async def get_user_1s(user_id:int, server="akatsuki", mode:int=0, relax:int=0, type=FirstPlacesEnum.all, date=str(datetime.datetime.now().date()), sort: str = ScoreSortEnum.date, desc: bool=True, score_filter: str = "", beatmap_filter: str = "", page:int=1, length:int=100,):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    first_places = list()
    yesterday = (date - datetime.timedelta(days=1))
    direction = sort_desc if desc else sort_asc
    with postgres.instance.managed_session() as session:
        query = session.query(DBUserFirstPlace).filter(DBUserFirstPlace.server == server,
                                                            DBUserFirstPlace.user_id == user_id,
                                                            DBUserFirstPlace.mode == mode,
                                                            DBUserFirstPlace.relax == relax,
                                                            DBUserFirstPlace.date == date,
                                                            ).join(DBScore).order_by(direction(getattr(DBScore, sort)))
        if score_filter:
            query = build_query(query.join(DBScore), DBScore, score_filter.split(","))
        if beatmap_filter:
            query = build_query(query.join(DBBeatmap), DBBeatmap, beatmap_filter.split(","))
        if type == "all":
            for first_place in query.offset((page-1)*length).limit(length).all():
                first_places.append(first_place.score)  
            total = query.count()
            return {'total': total, 'scores': first_places}
        elif type == "new":
            new = list()
            for first_place in query.all():
                if (old := session.query(DBUserFirstPlace).filter(
                    DBUserFirstPlace.date == yesterday,
                    DBUserFirstPlace.score_id == first_place.score_id
                )).first() is None:
                    new.append(first_place)
            offset = (page-1)*length
            total = len(new)
            if len(new) < offset:
                return {'total': total, 'scores': list()}
            first_places = list()
            for first_place in new[offset:offset+length]:
                first_places.append(first_place.score)  
            return {'total': total, 'scores': first_places}
        elif type == "lost":
            lost = list()
            for first_place in session.query(DBUserFirstPlace).filter(DBUserFirstPlace.server == server,
                                                            DBUserFirstPlace.user_id == user_id,
                                                            DBUserFirstPlace.mode == mode,
                                                            DBUserFirstPlace.relax == relax,
                                                            DBUserFirstPlace.date == yesterday,
                                                            ).all():
                if (new := session.query(DBUserFirstPlace).filter(
                    DBUserFirstPlace.date == date,
                    DBUserFirstPlace.score_id == first_place.score_id
                )).first() is None:
                    lost.append(first_place)
            offset = (page-1)*length
            total = len(lost)
            if len(lost) < offset:
                return {'total': total, 'scores': list()}
            first_places = list()
            for first_place in lost[offset:offset+length]:
                first_places.append(first_place.score)  
            return {'total': total, 'scores': first_places}

@app.get("/user/first_places/all")
async def get_user_1s(server="akatsuki", mode:int=0, relax:int=0, date=str(datetime.datetime.now().date()), sort: str = ScoreSortEnum.date, desc: bool=True, score_filter: str = "", beatmap_filter: str = "", page:int=1, length:int=100,):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    first_places = list()
    direction = sort_desc if desc else sort_asc
    with postgres.instance.managed_session() as session:
        query = session.query(DBUserFirstPlace).filter(DBUserFirstPlace.server == server,
                                                            DBUserFirstPlace.mode == mode,
                                                            DBUserFirstPlace.relax == relax,
                                                            DBUserFirstPlace.date == date,
                                                            ).join(DBScore).order_by(direction(getattr(DBScore, sort)))
        if score_filter:
            query = build_query(query.join(DBScore), DBScore, score_filter.split(","))
        if beatmap_filter:
            query = build_query(query.join(DBBeatmap), DBBeatmap, beatmap_filter.split(","))
        for first_place in query.offset((page-1)*length).limit(length).all():
            first_places.append(first_place.score)  
        total = query.count()
        return {'total': total, 'scores': first_places}


@app.get("/user/clears")
async def get_user_clears(user_id:int, server="akatsuki", mode:int=0, relax:int=0, date=str(datetime.datetime.now().date()), page:int=1, completed=3, score_filter: str = "", beatmap_filter: str = "", sort: str = ScoreSortEnum.date, desc: bool=True, length:int=100,):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    scores = list()
    direction = sort_desc if desc else sort_asc
    with postgres.instance.managed_session() as session:
        query = session.query(DBScore).filter(DBScore.server == server,
                                                            DBScore.user_id == user_id,
                                                            DBScore.mode == mode,
                                                            DBScore.relax == relax,
                                                            DBScore.completed == completed
                                                            ).order_by(direction(getattr(DBScore, sort)))
        if score_filter:
            query = build_query(query, DBScore, score_filter.split(","))
        if beatmap_filter:
            query = build_query(query.join(DBBeatmap), DBBeatmap, beatmap_filter.split(","))
        for score in query.offset((page-1)*length).limit(length).all():
            scores.append(session.query(DBScore).filter(DBScore.score_id == score.score_id).first())  
        total = query.count()
        return {'total': total, 'scores': scores}

@app.get("/user/clears/all")
async def get_all_clears( server="akatsuki", mode:int=0, relax:int=0, date=str(datetime.datetime.now().date()), page:int=1, completed=3, score_filter: str = "", beatmap_filter: str = "", sort: str = ScoreSortEnum.date, desc: bool=True, length:int=100,):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    scores = list()
    direction = sort_desc if desc else sort_asc
    with postgres.instance.managed_session() as session:
        query = session.query(DBScore).filter(DBScore.server == server,
                                                            DBScore.mode == mode,
                                                            DBScore.relax == relax,
                                                            DBScore.completed == completed
                                                            ).order_by(direction(getattr(DBScore, sort)))
        if score_filter:
            query = build_query(query, DBScore, score_filter.split(","))
        if beatmap_filter:
            query = build_query(query.join(DBBeatmap), DBBeatmap, beatmap_filter.split(","))
        for score in query.offset((page-1)*length).limit(length).all():
            scores.append(session.query(DBScore).filter(DBScore.score_id == score.score_id).first())  
        total = query.count()
        return {'total': total, 'scores': scores}


@app.get("/user/rank")
async def get_user_leaderboard(user_id: int, server="akatsuki", date=str(datetime.datetime.now().date()), mode:int=0, relax:int=0, type: str = TypeEnum.pp):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    with postgres.instance.managed_session() as session:
        if date != datetime.datetime.now().date():
            if (stats := session.get(DBStats, (user_id, server, mode, relax, date))) is not None:
                if type == "pp":
                    return {'global_rank': stats.global_rank, 'country_rank': stats.country_rank}
                else:
                    return {'global_rank': stats.global_score_rank, 'country_rank': stats.country_score_rank}
        else:
            model = DBLiveUser if type == 'pp' else DBLiveUserScore
            if (stats := session.get(model, (server, user_id, mode, relax))) is not None:
                return {'global_rank': stats.global_rank, 'country_rank': stats.country_rank}
        return {'global_rank': -1, 'country_rank': -1}

@app.get("/user/info")
async def get_user_info(user_id:int, server="akatsuki"):
    with postgres.instance.managed_session() as session:
        return session.get(DBUser, (user_id, server))

@app.get("/clan/info")
async def get_clan_info(clan_id:int, server="akatsuki"):
    with postgres.instance.managed_session() as session:
        return session.gebeatmap_setst(DBClan, (server, clan_id))

@app.get("/clan/members")
async def get_clan_members(clan_id:int, server="akatsuki"):
    members = list()
    with postgres.instance.managed_session() as session:
        for member in session.query(DBUser).filter(DBUser.server == server, DBUser.clan == clan_id).all():
            members.append(member)
        return members

@app.get("/clan/stats")
async def get_clan_stats(clan_id:int, server="akatsuki", mode:int=0, relax:int=0,date=str(datetime.datetime.now().date())):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    with postgres.instance.managed_session() as session:
        return session.get(DBClanStats, (server, clan_id, mode, relax, date))

@app.get("/beatmaps/server_sets")
async def get_sets():
    server_list = {}
    for server in servers:
        server_list[server.server_name] = server.beatmap_sets
    return server_list

@app.get("/beatmaps/list")
async def get_beatmaps(set_name, ranked_status: int = 1, mode: int = 0, page: int = 1, length: int = 100, beatmap_filter: str=""):
    beatmaps = list()
    with postgres.instance.managed_session() as session:
        query = session.query(DBBeatmap).filter(
            DBBeatmap.mode == mode,
            DBBeatmap.ranked_status[set_name].astext.cast(Integer) == ranked_status
        )
        if beatmap_filter:
            query = build_query(query, DBBeatmap, beatmap_filter.split(","))
        for beatmap in query.offset((page-1)*length).limit(length):
            beatmaps.append(beatmap)
    return beatmaps

def main():
    uvicorn.run(app, host="0.0.0.0", port=4269)