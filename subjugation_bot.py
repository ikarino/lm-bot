from discord.ext import commands
from dotenv import load_dotenv
import discord

import os
import traceback
from firestore import MyFirestore

load_dotenv(override=True)

INITIAL_EXTENSIONS = [
    'cogs.aggregate_cog',
    'cogs.utility_cog',
]
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

class SubjugationBot(commands.Bot):
    def __init__(self, command_prefix):
        super().__init__(command_prefix)
        for cog in INITIAL_EXTENSIONS:
            try:
                self.load_extension(cog)
            except Exception:
                traceback.print_exc()
        self.db = MyFirestore()

    async def on_ready(self):
        print('ログインしました')

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandNotFound):
            await ctx.send("知らないコマンドだよ")
        elif isinstance(error, commands.errors.CommandInvokeError):
            await ctx.send(embed=discord.Embed(
                title="処理例外が発生しました",
                description=error,
                colour=discord.Colour.red()
            ))

    
if __name__ == "__main__":
    bot = SubjugationBot(command_prefix='!')
    bot.run(TOKEN)