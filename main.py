import asyncio
from functools import partial

import rapidjson
import discord
from discord.ext import tasks

import config
import utils
from blockchain_monitor import BlockchainMonitor
from src.exportal import exportal


def stringify_txn(txn):
    return rapidjson.dumps(txn, indent=4, write_mode=rapidjson.WM_PRETTY)

    # user = txn.transactor.name if txn.transactor.name else "an anonymous user"
    # cauc_coins = utils.abbreviate_number(txn.creator_coins, 3)
    # usd = utils.format_as_usd(txn.usd, roundn=True)

    # sign, action = ('+', "BOUGHT") if txn.operation_type == "buy" else ('-', "SOLD")
    # return f"""```diff\n{sign} {user} just {action} {cauc_coins} (~{usd}) CAUC!```"""


@tasks.loop(seconds=0)
async def main_loop():
    parsed_txns = await exportal.get_from_sync()

    futures = [channel.send(stringify_txn(txn)) for txn in parsed_txns]
    for future in asyncio.as_completed(futures):
        await future

    await exportal.pass_to_sync(0)


@tasks.loop(hours=6)
async def check_in():
    if check_in.current_loop != 0:
        await channel.send("I'm still alive!")


@main_loop.before_loop
@check_in.before_loop
async def wait_until_ready():
    await bot.wait_until_ready()

    global channel
    if not channel:
        channel = bot.get_channel(config.DISCORD_CHANNEL_ID)
        await channel.send("I'm alive!")


if __name__ == '__main__':
    bot, channel = discord.Client(), None
    monitor = BlockchainMonitor(creator_key=config.CREATOR_KEY)

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, partial(monitor.main_loop, checks_per_minute=10))

    main_loop.start()
    check_in.start()
    bot.run(config.DISCORD_TOKEN, bot=True, reconnect=True)
