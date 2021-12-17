import glob
import json
import os
import re


def parse_text(full_path, txt: str):
    def split_last_space(s):
        i = s.rfind(" ")
        return s[:i - 1], s[i + 1:]

    txt = txt.replace("*", "")
    txt = re.findall(r"[\w \d]+: +\d+\w", txt)
    txt = [split_last_space(s.lower().lstrip()) for s in txt]
    txt = [(s[0], *(re.findall(r'[A-Za-z]+|[0-9]+', s[1]))) for s in txt]
    txt = list(filter(lambda x: len(x) == 3, txt))
    txt = [(s[0], int(s[1]), s[2]) for s in txt]

    stat_match = {
        "m": "time_played",
        "g": "scorers",
        "c": "cs",
        "s": "saves",
        "a": "assisters",
        "o": "own goals"
    }
    res = {"time_played": {}, "scorers": {}, "assisters": {}, "cs": {}, "saves": {}, "own goals": {}}
    for player, n, stat in txt:
        res[stat_match[stat]][player] = n

    with open(full_path, "w+") as f:
        json.dump(res, f, indent=4)


def delete_non_4v4():
    for filename in glob.glob("bff/*.json"):
        with open(filename, "r") as f:
            game = json.load(f)
        if len(game["time_played"]) < 6:
            os.remove(filename)
