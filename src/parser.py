import glob
import json
import os
import re

from src.players import update_stats


class Game:
    stat_match = {
        "m": "time_played",
        "g": "scorers",
        "cs": "cs",
        "s": "saves",
        "a": "assisters",
        "og": "own goals"
    }

    @staticmethod
    def parse(path, text: str):
        t = text.splitlines()
        t = [s[4:].lower().split(":** ") for s in t if s.startswith(">")]
        t = [(x, *y.split(" ")) for x, y in t]
        d = {}
        for name, *stats in t:
            if name in d:
                d[name] += stats
            else:
                d[name] = stats
        if len(d) <= 7:
            return

        game = {"time_played": {}, "scorers": {}, "assisters": {}, "cs": {}, "saves": {}, "own goals": {}}
        for name, stats in d.items():
            for stat in stats:
                number_stat_name = re.findall(r"\d+|\w+", stat)
                try:
                    number, stat_name = int(number_stat_name[0]), Game.stat_match[number_stat_name[1]]
                except KeyError:
                    if "m" in number_stat_name[-1]:
                        number, stat_name = int(number_stat_name[0]), Game.stat_match["m"]
                    else:
                        continue

                game[stat_name][name] = number

        with open(path, "w+") as file:
            json.dump(game, file, indent=4)


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
    print("deleting 4v4s")
    for filename in glob.glob("bff/*.json"):
        with open(filename, "r") as f:
            game = json.load(f)
        if len(game["time_played"]) < 6:
            os.remove(filename)


def reload_all_data():
    print("updating stats")
    json.dump({}, open("players/players.json", "w+"))
    for filename in glob.glob("bff/*.json"):
        update_stats(filename)
    print("finished updating")
