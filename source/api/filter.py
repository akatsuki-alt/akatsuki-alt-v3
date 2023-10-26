from sqlalchemy.orm.query import Query
from typing import TypedDict
import re

OPS = ['!=', '==', '<', '>', 'in'] 

def build_query(query: Query, model, conditions=[]):
    for condition in conditions:
        for op in OPS:
            if op in condition:
                break
        attr, to_match = condition.split(op)
        match op:
            case "!=":
                query = query.filter(getattr(model, attr) != to_match)
            case "==":
                query = query.filter(getattr(model, attr) == to_match)
            case "<":
                query = query.filter(getattr(model, attr) < to_match)
            case ">":
                query = query.filter(getattr(model, attr) > to_match)
            case "in":
                query = query.filter(to_match in getattr(model, attr))
    return query