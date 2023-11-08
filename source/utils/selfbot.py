from utils.api.request import RequestHandler
from typing import *
import json
import time

HEADERS = {}

with open("/app/headers.json") as f:
    HEADERS = json.load(f)

handler = RequestHandler(req_min=5, headers=HEADERS)

class Author(TypedDict):
    bot: bool
    id: str
    username: str
    avatar: str
    discriminator: str

class Field(TypedDict):
    name: str
    value: str
    inline: bool

class EmbedAuthor(TypedDict):
    name: str
    url: str
    icon_url: str
    proxy_icon_url: str

class EmbedImage(TypedDict):
    url: str
    proxy_url: str
    width: int
    height: int

class Embed(TypedDict):
    type: str
    title: str
    url: str
    description: str
    color: int
    fields: List[Field]
    author: EmbedAuthor
    image: EmbedImage

class Message(TypedDict):
    id: str
    type: int
    content: str
    channel_id: str
    author: Author
    attachments: List
    embeds: List[Embed]
    mention_roles: List
    pinned: bool
    mention_everyone: bool
    tts: bool
    timestamp: str
    edited_timestamp: str
    flags: int
    components: List
    webhook_id: int
    hit: bool

def search_channel(guild_id=365406575893938177, channel_id=647363000629460992, offset=0) -> List[Message]:
    attempts = 1
    while attempts < 10:
        req = handler.get(f"https://discord.com/api/v9/guilds/{guild_id}/messages/search?channel_id={channel_id}&offset={offset}")
        if req.ok:
            break
        time.sleep(2)
        attempts += 1
    if not req.ok:
        return
    return req.json()["messages"]
