import json
import os

import discord
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands import has_permissions
from dotenv import load_dotenv

from src.decorators import string_to, apply_predicate
from src.parser import parse_text, Game
from src.players import update_stats, Server, Matching

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()


def get_prefix(client, message):  # first we define get_prefix
    with open('prefixes.json', 'r') as f:  # we open and read the prefixes.json, assuming it's in the same file
        prefixes = json.load(f)  # load the json as prefixes

    try:
        id = str(message.guild.id)
    except Exception:
        id = 0
    return prefixes[id] if id in prefixes else "!"  # receive the prefix for the guild id given


BOT: Bot = commands.Bot(command_prefix=get_prefix, case_insensitive=True, intents=intents,
                        chunk_guilds_at_startup=False)
server = None


@BOT.command(pass_context=True)
@has_permissions(administrator=True)
async def set_prefix(ctx, prefix="!"):
    """Set a new prefix for this bot.

    With no args, this resets the prefix to the default one."""
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    prefixes[str(ctx.guild.id)] = prefix

    with open('prefixes.json', 'w') as f:
        json.dump(prefixes, f, indent=4)

    await ctx.send(f'Prefix changed to: {prefix}')


@BOT.event
async def on_ready():
    """On ready event."""
    print(f'{BOT.user} has connected\n')


@BOT.event
async def on_guild_remove(guild):  # when the bot is removed from the guild
    with open('prefixes.json', 'r') as f:  # read the file
        prefixes = json.load(f)

    try:
        prefixes.pop(str(guild.id))  # find the guild.id that bot was removed from
    except KeyError:
        pass

    with open('prefixes.json', 'w') as f:  # deletes the guild.id as well as its prefix
        json.dump(prefixes, f, indent=4)


def get_prefix2(id):
    """Return the prefix of this bot for a specific guild or ! as default"""
    with open('prefixes.json', 'r') as f:
        prefixes = json.load(f)

    return prefixes[id] if id in prefixes else "!"


async def send_error(ctx, desc, read_help=True):
    try:
        helper = f"Read !help {ctx.invoked_with}" * read_help
        desc = desc[desc.find(":") + 1:]
        await ctx.send(embed=Embed(title="Error !", color=0x000000,
                                   description=f"{str(desc)}\n{helper}"))
    except Exception:
        pass


async def send_global_error(ctx, desc):
    try:
        desc = desc[desc.find(":") + 1:]
        await ctx.send(embed=Embed(title="Error !", color=0x000000,
                                   description=f"{str(desc)}"))
    except Exception:
        pass


@BOT.command(pass_context=True, hidden=True)
async def parse2(ctx):
    print("parsing")
    channel: discord.abc.Messageable = await BOT.fetch_channel(726932424172371968)
    async for message in channel.history(limit=10):
        try:
            embed = message.embeds[0]
        except IndexError:
            continue
        full_path = os.path.join("bff2/", embed.title.split("#")[-1] + ".json")
        if os.path.isfile(full_path):
            print(full_path + " already exists")
            continue

        d_embed = embed.to_dict()
        game = d_embed["fields"][0]["value"] + d_embed["fields"][1]["value"]
        Game.parse(full_path, game)
    await ctx.send("Finished parsing")


def get_real_time(total_minutes):
    hours = total_minutes // 60
    mins = total_minutes % 60

    hours = f"0{hours}" if hours < 10 else str(hours)
    mins = f"0{mins}" if mins < 10 else str(mins)

    return f"{hours:<4}h{mins:>3}m"


@BOT.command(pass_context=True, aliases=["s", "stats"])
async def stat(ctx, *player_name):
    """Get the stat based of the name.


    Hello I made a new bot so you can see your all times stats in reports-scrim and reports-official

    - !stat <haxball_nickname>

    - It works weird with non alphanumeric nicknames (emojis and dots an and stuff)

    """
    player_name = " ".join(player_name).lower()
    player: dict[str] = server.players.get_player(player_name)
    desc = "```py\n"
    desc += f'{"name":<15} {player_name:<20} {"stat / time %":<10}\n'
    total_minutes = player["time"]
    desc += f'{"time":<15} {total_minutes:<20} {get_real_time(total_minutes):<10}\n'
    for s in ('goals', 'assists', 'saves', 'cs', 'own goals'):
        val = player[s]
        ratio = val / total_minutes
        desc += f'{s:<15} {val:<20} {ratio * 100:<14.3f}\n'

    try:
        alts = player["alts"]
        str_alts = ", ".join([str(p) for p in alts])
        desc += f'{"alts":<15} {str_alts}\n'
    except KeyError:
        desc += f'{"alts":<15} {"No alt found"}\n'
    desc += "```"

    await ctx.send(embed=Embed(title=player_name, description=desc))


def time_key(sorted_players, i, end, index):
    desc = '```\n'
    desc += f'pos {"name":<20} {"mins":>6} {"total":>10}\n\n'
    while i < end and i < len(sorted_players) and index < len(sorted_players):
        v = sorted_players[index]
        i += 1
        desc += f'{"0" if i <= 9 else ""}{i}) {v[0]:<20} {v[1]:>6} {get_real_time(v[1]):>10}\n'

        index += 1

    desc += '```'
    return desc


def basic_keys(sorted_players, i, end, index, key):
    desc = '```\n'
    desc += f'pos {"name":<20} {key:>10} {"time":>6} {"%":>10}\n\n'
    while i < end and i < len(sorted_players) and index < len(sorted_players):
        v = sorted_players[index]
        i += 1
        desc += f'{"0" if i <= 9 else ""}{i}) {v[0]:<20} {v[1]:>10} {v[2]:>6} {(v[1] / v[2] if v[2] != 0 else v[1]) * 100:>10.2f}\n'

        index += 1

    desc += '```'
    return desc


def embed_leaderboard(start_page, players, key):
    i = 20 * (start_page - 1)
    index = i
    end = 20 * start_page
    if key == "time":
        desc = time_key(players, i, end, index)
    else:
        desc = basic_keys(players, i, end, index, key)
    nb_pages = 1 + len(server.players.players) // 20
    return Embed(title=f"{key} leaderboard", description=desc) \
        .set_footer(text=f"[ {start_page} / {nb_pages} ]")


@BOT.command(pass_context=True, aliases=["lb"])
@string_to(int, (-1,))
@apply_predicate(lambda x: x > 0, (-1,), "must be positive")
async def leaderboard(ctx, key, start_page=1):
    """See the leaderboard of a specific stat.

    Available stats: time, goals, assists, saves, cs, og
    Page: the number of the page you want to show, 20 players per page
    """
    sorted_players = server.sorted.sort_players_by(key)
    embed = embed_leaderboard(start_page, sorted_players, key)

    await ctx.send(embed=embed)


@BOT.command(pass_context=True, aliases=["r", "rlb"])
@string_to(int, (-1, -2))
@apply_predicate(lambda x: x >= 0, (-1, -2), "must be positive")
async def ratio_leaderboard(ctx, key, min_time=0, start_page=1):
    """See the ratio leaderboard of a specific stat.

    Available stats: time, goals, assists, saves, cs, og
    Page: the number of the page you want to show, 20 players per page
    Min time: the minimum time you want players to have played in order to appear in the leaderboard
    """

    sorted_players = [p for p in sorted(server.sorted.sort_players_by(key),
                                        reverse=True,
                                        key=lambda x: x[1] / x[2] if x[2] != 0 else x[1])
                      if p[2] >= min_time
                      ]
    embed = embed_leaderboard(start_page, sorted_players, key)

    await ctx.send(embed=embed)


@BOT.command(pass_context=True, aliases=["m"])
async def merge(ctx, *alts):
    """Associate several nicknames with one player.

    Exemple:
        !merge anddy + nd + steely knives + rejuvenation

    The associated nickname will be something like "* anddy"
        (star first, then the first name you submitted)
    This will not erase other alts from the leaderboard as you are all retarded and could fuck up the database

    However you can ask for a nickname deletion in #merge-demands to not have yourself 50 times in the leaderboard
    We will check your nicknames before deleting, if it's not yours, you can fuck yourself.
    You must put "+" between every player
    """
    nicknames = " ".join(alts).split(" + ")
    new_player_name = f"*{nicknames[0]}"
    if new_player_name in server.players:
        raise ValueError(f"Error : There is already a merged player called {new_player_name}")
    players = [server.players.get_player(player) for player in nicknames]
    stats = {s: 0 for s in Matching.player_to_game}
    for p in players:
        for name in stats:
            stats[name] += p[name]
    stats["alts"] = nicknames
    server.players.add_player(new_player_name, stats)
    server.sorted.build(server.players)
    await ctx.send(embed=Embed(description=f"Merged player of {nicknames} created called `{new_player_name}`"))


@BOT.command(pass_context=True, aliases=["rm"])
async def delete(ctx, player):
    """Delete player from the database.

    Only usable by Anddy."""
    if not ctx.author.id == 339349743488729088:
        raise ValueError("Error : You do not have the permission to use that command, only anddy can")
    server.players.delete_player(player)
    server.sorted.build(server.players)
    await ctx.send(embed=Embed(description=f"Delete player {player} from the database"))


@BOT.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        return await send_error(ctx, f"The command doesn't exist, check `!fcmds {ctx.invoked_with}` !", read_help=False)
    elif isinstance(error, commands.errors.CommandInvokeError):
        if isinstance(error.original, ValueError):
            if str(error.original).startswith("Error"):
                return await send_error(ctx, str(error.original))
            if str(error.original).startswith("Global"):
                return await send_global_error(ctx, str(error.original))
    raise error


if __name__ == '__main__':
    # delete_non_4v4()
    # Updater().update_all()
    server = Server()
    BOT.run(TOKEN)
