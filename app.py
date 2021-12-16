import json
import os

import discord
from discord import Embed
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands import has_permissions
from dotenv import load_dotenv

from src.parser import parse_text
from src.players import update_stats, get_player

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
async def parse(ctx):
    print("parsing")
    channel: discord.abc.Messageable = await BOT.fetch_channel(726932351241814117)
    async for message in channel.history(limit=None):
        try:
            embed = message.embeds[0]
        except IndexError:
            continue
        full_path = os.path.join("bff/", embed.title.split("#")[-1] + ".json")
        if os.path.isfile(full_path):
            print(full_path + " already exists")
            continue

        d_embed = embed.to_dict()
        game = d_embed["fields"][0]["value"] + d_embed["fields"][1]["value"]
        parse_text(full_path, game)
        update_stats(full_path)

    await ctx.send("Finished parsing")


@BOT.command(pass_context=True)
async def stat(ctx, *player_name):
    """Get the stat based of the name.


    Hello I made a new bot so you can see your all times stats in reports-scrim

    - !stat <haxball_nickname> is the only command for now

    - It works weird with non ascii nicknames (emojis and accents and stuff)

    - If you used alts, rip, i'll soon make a !merge command that will show stats of your alts
    """
    player_name = " ".join(player_name).lower()
    player: dict[str, int] = get_player(player_name)
    desc = "```py\n"
    desc += f"{'name':<10} {'time':^8} {'goals':^8} {'assists':^8} {'saves':^8} {'cs':^8}\n"
    p = player
    desc += f"{player_name:<10} {p['time']:^8} {p['goals']:^8} {p['assists']:^8} {p['saves']:^8} {p['cs']:^8}\n"
    desc += "```"
    await ctx.send(embed=Embed(title=player_name, description=desc))


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
    BOT.run(TOKEN)
