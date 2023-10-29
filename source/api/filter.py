from sqlalchemy.orm.query import Query
from sqlalchemy import Integer
from typing import TypedDict
import re

OPS = ['!=', '==', '<', '>', 'in'] 

def build_query(query: Query, model, conditions=[]):
    for condition in conditions:
        for op in OPS:
            if op in condition:
                break
        attr, to_match = condition.split(op)
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
                case "in":
                    query = query.filter(to_match in getattr(model, attr))
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
                case "in":
                    query = query.filter(to_match in getattr(model, attr))
        return query