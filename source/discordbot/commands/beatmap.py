from typing import List
from akatsuki_pp_py import Beatmap, Calculator

from discord import Message, Embed
from discordbot.bot import Command
from utils.parser import parse_args
from utils.api.akataltapi import instance
from datetime import datetime, timedelta
from utils.beatmaps import get_calc_beatmap

def get_beatmap_embed(beatmap_id: int):
    beatmap = instance.get_beatmap(beatmap_id)
    if not beatmap:
        return
    nominator = None
    if beatmap.nominator:
        for server, nominators in beatmap.nominator.items():
            if nominators and nominators.lower() != "unknown":
                nominator = (server, nominators)
    approved_date = datetime.fromtimestamp(beatmap.approved_date).strftime("%m/%d/%Y")
    pp = None
    ranked_status = "Graveyard"
    match beatmap.ranked_status['akatsuki']:
        case 1:
            ranked_status = "ranked"
        case 2:
            ranked_status = "approved"
        case 3:
            ranked_status = "qualified"
        case 4:
            ranked_status = "loved"
    calc_beatmap = get_calc_beatmap(beatmap_id)
    modes = ['osu!', 'taiko', 'ctb', "mania"]
    if calc_beatmap:
        calc_pp = []
        try:
            for mod in [0, 64, 80, 128, 192, 208, 8192, 8256, 8272]:
                calc = Calculator(mods=mod)
                calc_pp.append(int(calc.performance(calc_beatmap).pp))
            pp = calc_pp
        except:
            pass
    embed = Embed(title=f"{beatmap.artist} - {beatmap.title} [{beatmap.version}] ({modes[beatmap.mode]})")
    embed.add_field(name="Mapper", value=f"{beatmap.mapper}")
    if nominator:
        embed.add_field(name=f"Nominator(s) ({nominator[0].title()})", value=f"{nominator[1]}")
    else:
        embed.add_field(name=f"Nominator(s)", value=f"Unknown")
    embed.add_field(name="Approved date", value=approved_date+f" ({ranked_status})")
    embed.add_field(name="CS/OD/AR", value=f"{beatmap.cs}/{beatmap.od}/{beatmap.ar}")
    embed.add_field(name="NM/DT/DTHR SR", value=f"{beatmap.stars_nm:.2f}*/{beatmap.stars_dt:.2f}*/{beatmap.stars_dthr:.2f}*")
    embed.add_field(name="Circles/Sliders", value=f"{beatmap.circles}/{beatmap.sliders}")
    embed.add_field(name="BPM", value=int(beatmap.bpm))
    embed.add_field(name="Length", value=f"{timedelta(seconds=beatmap.length)}")
    embed.add_field(name="Max combo", value=f"{beatmap.max_combo}x")
    if pp:
        embed.add_field(name="NM/DT/DTHR PP", value=f"VN: {pp[0]}/{pp[1]}/{pp[2]}")
        embed.add_field(name="NM/DT/DTHR PP", value=f"RX: {pp[3]}/{pp[4]}/{pp[5]}")
        embed.add_field(name="NM/DT/DTHR PP", value=f"AP: {pp[6]}/{pp[7]}/{pp[8]}")
    embed.set_image(url=f"https://assets.ppy.sh/beatmaps/{beatmap.beatmap_set_id}/covers/cover@2x.jpg")
    return embed

class BeatmapCommand(Command):
    
    def __init__(self) -> None:
        super().__init__("beatmap", "check beatmap info", ["beatmap", "b"])
    
    async def run(self, message: Message, arguments: List[str]):
        parsed = parse_args(arguments, unparsed=True)
        if not parsed['unparsed']:
            await message.reply("currently not implemented")
            return
        if len(parsed['unparsed']) > 1: # Beatmap search
            await message.reply("currently not implemented")
            return
        else:
            to_parse: str = parsed['unparsed'][0]
            if to_parse.isnumeric():
                embed = get_beatmap_embed(int(to_parse))
            elif "osu.ppy.sh/beatmapsets/" in to_parse or "osu.ppy.sh/b/" in to_parse:
                beatmap_id = to_parse.split("/")[-1]
                if not beatmap_id.isnumeric():
                    await message.reply(f"Invalid url!")
                    return
                embed = get_beatmap_embed(int(beatmap_id))
            if not embed:
                await message.reply("Map not found!")
            else:
                await message.reply(embed=embed)
            return
                