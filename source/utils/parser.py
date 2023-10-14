from typing import *

def parse_args(args: List[str], unparsed=False):
    parsed_args = {}
    if unparsed:
        parsed_args['unparsed'] = []
    for arg in args:
        arg = arg.split("=")
        if len(arg) != 2:
            if unparsed:
                parsed_args['unparsed'].append(arg[0])
            continue
        parsed_args[arg[0]] = arg[1]
    return parsed_args