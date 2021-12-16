import glob
import json


def plus_or_zero(dico, half, key, p):
    try:
        return dico[half][key][p]
    except KeyError:
        return 0


class Player:
    def __init__(self, name):
        self.name = name
        self.time = 0
        self.goals = 0
        self.assists = 0
        self.saves = 0
        self.cs = 0

    def add(self, stat_name, value):
        setattr(self, stat_name, value + getattr(self, stat_name))

    def __str__(self):
        return "\n".join([f"{prop} : {val}" for prop, val in self.__dict__.items()])


players_dict = {
    "thegoal": Player("thegoal"),
    "tintin": Player("tintin"),
    "anddy": Player("anddy"),
    "hassi": Player("hassi"),
    "blaaster": Player("blaaster"),
    "gouiri": Player("gouiri"),
    "screed": Player("screed"),
    "iliess": Player("iliess"),
    "thors": Player("thors"),
    "toshiba": Player("toshiba"),
    "allen": Player("allen"),
}


def load_data():
    datas = []
    for file in glob.glob("champions/*.json"):
        with open(file) as json_file:
            datas.append(json.load(json_file))
    return datas


def parse(data_list, players):
    matching_stats = {
        "time": "time_played",
        "goals": "scorers",
        "assists": "assisters",
        "cs": "cs",
        "saves": "saves"
    }
    for data in data_list:
        for name, player in players.items():
            for player_stat, offi_stat in matching_stats.items():
                for half in ("half1", "half2"):
                    player.add(player_stat, plus_or_zero(data, half, offi_stat, name))



if __name__ == '__main__':
    datas = load_data()
    parse(datas, players_dict)

    with open("stats", "w+") as f:
        f.write("```py\n")
        f.write(f"{'name':<10} {'time':^8} {'goals':^8} {'assists':^8} {'saves':^8} {'cs':^8}\n")

        for p in sorted(players_dict.values(), key=lambda x: -x.time):
            f.write(f"{p.name:<10} {p.time:^8} {p.goals:^8} {p.assists:^8} {p.saves:^8} {p.cs:^8}\n")
        f.write("```")

