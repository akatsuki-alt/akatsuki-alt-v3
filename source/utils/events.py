from typing import Dict, Generator, Callable
from redis import Redis

import logging
import config

class EventQueue:
    def __init__(self, name: str, connection: Redis) -> None:
        self.redis = connection
        self.name = name

        self.events: Dict[str, Callable] = {}
        self.logger = logging.getLogger(self.name)

        self.channel = self.redis.pubsub()

    def register(self, event_name: str):
        """Register an event"""
        def wrapper(callback: Callable):
            self.events[event_name] = callback
            self.logger.debug(
                f'Registered new event: "{event_name}"'
            )
            return callback
        return wrapper

    def submit(self, event: str, *args, **kwargs):
        """Push an event to the queue"""
        self.redis.publish(self.name, str((event, args, kwargs)))
        self.logger.debug(f'Submitted event "{event}" to pubsub channel')

    def listen(self) -> Generator:
        """Listen for events from the queue"""
        self.channel.subscribe(self.name)
        self.logger.info('Listening to pubsub channel...')

        for message in self.channel.listen():
            try:
                if message['data'] == 1: continue
                name, args, kwargs = eval(message['data'])
                self.logger.debug(
                    f'Got event for "{name}" with {args} and {kwargs}'
                )
                yield self.events[name], args, kwargs
            except KeyError:
                self.logger.warning(
                    f'No callback found for "{name}"'
                )
            except Exception as e:
                self.logger.warning(
                    f'Failed to evaluate task: {e}'
                )

queue = EventQueue(name="events", connection=Redis())