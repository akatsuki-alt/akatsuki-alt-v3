from utils.logger import get_logger
from discord.ext import tasks
from queue import Queue

import utils.events as events

queue = Queue()

logger = get_logger('discord_bot.tasks')

@events.queue.register('user_banned')
def user_banned(user_id: int, server: str, linked: bool):
    queue.put({'event': 'user_banned', 'user_id': user_id, 'server': server, 'linked': linked})
    logger.info("triggered event")

@tasks.loop(seconds=10)
async def process_events():
    while True:
        try:
            event = queue.get(block=False)
        except:
            break
        logger.info(f"Received event {event}")


