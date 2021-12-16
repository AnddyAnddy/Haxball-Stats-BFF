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


def create_player(players_db, player):
    players_db[player] = {stat: 0 for stat in Matching.player_to_game}


def update_stats(path_to_last_game):
    with open("players/players.json", "r") as db:
        players_db = json.load(db)
    with open(path_to_last_game, "r") as f:
        game: dict[str, dict[str, int]] = json.load(f)
        # print(players_db)
        # print(game)

        for stat, players in game.items():
            convert_to_player_stat = Matching.game_to_player[stat]
            for player, n in players.items():
                if player not in players_db:
                    players_db[player] = {stat: 0 for stat in Matching.player_to_game}
                players_db[player][convert_to_player_stat] += n

        # print(players_db)
    with open("players/players.json", "w+") as db:
        json.dump(players_db, db, indent=4)


def get_player(player):
    with open("players/players.json", "r") as db:
        players_db = json.load(db)
    try:
        return players_db[player]
    except KeyError:
        raise ValueError("Error : " + player + " not in my database")


if __name__ == '__main__':
    update_stats("../bff/2112152242401.json")
