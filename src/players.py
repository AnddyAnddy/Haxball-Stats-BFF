import datetime
import glob
import json


class Matching:
    player_to_game = {
        "time": "time_played",
        "goals": "scorers",
        "assists": "assisters",
        "cs": "cs",
        "saves": "saves",
        "own goals": "own goals"
    }
    game_to_player = {
        "time_played": "time",
        "scorers": "goals",
        "assisters": "assists",
        "cs": "cs",
        "saves": "saves",
        "own goals": "own goals"
    }


class Updater:
    def __init__(self):
        self.players_db = {}

    def update_all(self):
        print("start the update all at time: ", datetime.datetime.now())
        json.dump({}, open("players/players.json", "w+"))
        for filename in glob.glob("bff/*.json"):
            with open(filename, "r") as f:
                game: dict[str, dict[str, int]] = json.load(f)
                for stat, players in game.items():
                    convert_to_player_stat = Matching.game_to_player[stat]
                    for player, n in players.items():
                        if player not in self.players_db:
                            self.players_db[player] = {stat: 0 for stat in Matching.player_to_game}
                        self.players_db[player][convert_to_player_stat] += n

        print("finished updating")
        with open("players/players.json", "w+") as db:
            json.dump(self.players_db, db, indent=4)
        print("finished dumping", datetime.datetime.now())


def update_stats(path_to_last_game):
    with open("players/players.json", "r") as db:
        players_db = json.load(db)
    with open(path_to_last_game, "r") as f:
        game: dict[str, dict[str, int]] = json.load(f)
        for stat, players in game.items():
            convert_to_player_stat = Matching.game_to_player[stat]
            for player, n in players.items():
                if player not in players_db:
                    players_db[player] = {stat: 0 for stat in Matching.player_to_game}
                players_db[player][convert_to_player_stat] += n

        # print(players_db)

    with open("players/players.json", "w+") as db:
        json.dump(players_db, db, indent=4)


class Players:

    def __init__(self):
        with open("players/players.json", "r") as db:
            self.players: dict = json.load(db)

    def get_player(self, player):
        try:
            return self.players[player]
        except KeyError:
            raise ValueError("Error : " + player + " not in my database")

    def add_player(self, player_name, stats):
        if player_name in self.players:
            raise ValueError(f"Error : Player {player_name} already in the database")
        self.players[player_name] = stats
        with open("players/players.json", "w+") as db:
            json.dump(self.players, db, indent=4)

    def delete_player(self, player_name):
        try:
            self.players.pop(player_name)
        except KeyError:
            raise ValueError(f"Error : Could not delete {player_name}, not in db")
        with open("players/players.json", "w+") as db:
            json.dump(self.players, db, indent=4)

    def __contains__(self, item):
        return item in self.players


class Sorted:
    valid_keys = {
        "time": "time",
        "goals": "goals",
        "assists": "assists",
        "og": "own goals",
        "cs": "cs",
        "saves": "saves",
    }

    def __init__(self, players: Players):
        self.time = []
        self.goals = []
        self.assists = []
        self.own_goals = []
        self.cs = []
        self.saves = []
        self.build(players)

    def sort_players_by(self, key):
        try:
            key = Sorted.valid_keys[key]
        except KeyError:
            raise ValueError(f"Error : You can not sort by this key `{key}`")
        return getattr(self, key)

    def build(self, players: Players):
        for key in Sorted.valid_keys.values():
            setattr(self, key,
                    [(k, v[key], v["time"]) for k, v in
                     sorted(players.players.items(), reverse=True, key=lambda item: item[1][key])])


class Server:
    def __init__(self):
        self.players: Players = Players()
        self.sorted = Sorted(self.players)


if __name__ == '__main__':
    update_stats("../bff/2112152242401.json")
