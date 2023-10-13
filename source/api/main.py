
import utils.postgres as postgres
from utils.database import *

from fastapi import FastAPI
import datetime
import uvicorn

app = FastAPI()

class TypeEnum(str, Enum):
    pp = "pp"
    score = "score"
    first_places = "1s"
    clears = "clears"

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
    orders = {'pp': 'global_rank', 'score': 'global_score_rank', 'total_score': 'total_score DESC', 'clears': 'clears DESC', '1s': 'first_places DESC'}
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
async def get_clan_leaderboard(server="akatsuki", mode:int=0, relax:int=0, page:int=1, length:int=100, type: str = TypeEnum.pp):
    length = min(100, length)
    users = []
    with postgres.instance.managed_session() as session:
        orders = {'pp': 'global_rank', '1s': 'global_rank_1s', 'score': 'ranked_score DESC', 'total_score': 'total_score DESC', 'play_count': 'play_count DESC'}
        order = orders['pp']
        if type in orders:
            order = orders[type]
        for stats in session.query(DBClanStats).filter(DBClanStats.server == server, DBClanStats.mode == mode, 
                                                     DBClanStats.relax == relax).order_by(
                                                         text(order)).offset((page-1)*length).limit(length).all():
            users.append(stats)
    return users


@app.get("/user/stats")
async def get_user(user_id:int, server="akatsuki", mode:int=0, relax:int=0,date=str(datetime.datetime.now().date())):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    with postgres.instance.managed_session() as session:
        return session.get(DBStats, (user_id, server, mode, relax, date))

@app.get("/user/first_places")
async def get_user_1s(user_id:int, server="akatsuki", mode:int=0, relax:int=0, date=str(datetime.datetime.now().date()), page:int=1, length:int=100,):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    first_places = list()
    with postgres.instance.managed_session() as session:
        for first_place in session.query(DBUserFirstPlace).filter(DBUserFirstPlace.server == server,
                                                            DBUserFirstPlace.user_id == user_id,
                                                            DBUserFirstPlace.mode == mode,
                                                            DBUserFirstPlace.relax == relax,
                                                            ).offset((page-1)*length).limit(length).all():
            first_places.append(session.query(DBScore).filter(DBScore.score_id == first_place.score_id).first())  
        total = session.query(DBUserFirstPlace).filter(DBUserFirstPlace.server == server,
                                                            DBUserFirstPlace.user_id == user_id,
                                                            DBUserFirstPlace.mode == mode,
                                                            DBUserFirstPlace.relax == relax,
                                                            ).count()
        return {'total': total, 'scores': first_places}

@app.get("/user/clears")
async def get_user_clears(user_id:int, server="akatsuki", mode:int=0, relax:int=0, date=str(datetime.datetime.now().date()), page:int=1, length:int=100,):
    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    scores = list()
    with postgres.instance.managed_session() as session:
        for score in session.query(DBScore).filter(DBScore.server == server,
                                                            DBScore.user_id == user_id,
                                                            DBScore.mode == mode,
                                                            DBScore.relax == relax,
                                                            ).offset((page-1)*length).limit(length).all():
            scores.append(session.query(DBScore).filter(DBScore.score_id == score.score_id).first())  
        total = session.query(DBScore).filter(DBScore.server == server,
                                                            DBScore.user_id == user_id,
                                                            DBScore.mode == mode,
                                                            DBScore.relax == relax,
                                                            ).count()
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
        return session.get(DBClan, (server, clan_id))

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
    
def main():
    uvicorn.run(app, host="0.0.0.0", port=4269)