from sqlalchemy.orm.query import Query
from sqlalchemy import Integer
import utils.mods as mods

OPS = ['!=', '==', '<', '>', 'has not', 'has']

def build_query(query: Query, model, conditions=[]):
    for condition in conditions:
        for op in OPS:
            if op in condition:
                break
        attr, to_match = condition.split(op)
        attr = attr.strip()
        to_match = to_match.strip()
        if "." in attr:
            attr, attr2 = attr.split(".")
            match op:
                case "!=":
                    query = query.filter(getattr(model, attr)[attr2].astext.cast(Integer) != to_match)
                case "==":
                    query = query.filter(getattr(model, attr)[attr2].astext.cast(Integer) == to_match)
                case "<":
                    query = query.filter(getattr(model, attr)[attr2].astext.cast(Integer) < to_match)
                case ">":
                    query = query.filter(getattr(model, attr)[attr2].astext.cast(Integer) > to_match)
                case "has":
                    query = query.filter(to_match in getattr(model, attr))
                case "has not":
                    query = query.filter(to_match not in getattr(model, attr))
        elif attr == "mods":
            mods_bit = mods.mods_from_string(to_match)
            print(mods_bit)
            match op:
                case "!=":
                    query = query.filter(getattr(model, attr) != mods_bit)
                case "==":
                    query = query.filter(getattr(model, attr) == mods_bit)
                case "has":
                    query = query.filter(getattr(model, attr).op("&")(mods_bit) > 0)
                case "has not":
                    query = query.filter(getattr(model, attr).op("&")(mods_bit) == 0)
        else:
            match op:
                case "!=":
                    query = query.filter(getattr(model, attr) != to_match)
                case "==":
                    query = query.filter(getattr(model, attr) == to_match)
                case "<":
                    query = query.filter(getattr(model, attr) < to_match)
                case ">":
                    query = query.filter(getattr(model, attr) > to_match)
                case "has":
                    query = query.filter(to_match in getattr(model, attr))
                case "has not":
                    query = query.filter(to_match not in getattr(model, attr))
        return query