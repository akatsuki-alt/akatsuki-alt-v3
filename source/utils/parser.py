from typing import *
from utils.selfbot import Embed

def parse_args(args: List[str], unparsed=False):
    parsed_args = {}
    if unparsed:
        parsed_args['unparsed'] = []
    for arg in args:
        arg = arg.split("=", maxsplit=1)
        if len(arg) != 2:
            if unparsed:
                parsed_args['unparsed'].append(arg[0])
            continue
        parsed_args[arg[0]] = arg[1]
    return parsed_args

def parse_akatsuki_embed(embed: Embed) -> [int, str]:
    if 'url' in embed and embed['url']: # new embed format
        beatmap_id = int(embed['url'].split("/")[-1])
        nominator = embed['author']['name'].split()[0]
        return beatmap_id, nominator
    else:
        if embed['fields'][3]['name'] == "Gamemode": # very old embed format
            beatmap_id = int(embed['fields'][4]['value'].split("/")[-1][:-1])
        else:
            beatmap_id = int(embed['fields'][3]['value'].split("/")[-1][:-1])
        nominator = embed['fields'][2]['value'].split("]")[0][1:]
        return beatmap_id, nominator