from ossapi import Ossapi
import logging
import config

client = Ossapi(client_id=config.OSU_CLIENT_ID, client_secret=config.OSU_API_KEY, token_directory=config.BASE_PATH+"/")
client.log.level = logging.ERROR
