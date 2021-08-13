# https://qiita.com/Lazialize/items/81f1430d9cd57fbd82fb
from discord.ext import commands
from dotenv import load_dotenv

import os
import traceback
from firestore import MyFirestore

load_dotenv(override=True)

# 読み込むコグの名前を格納しておく。
INITIAL_EXTENSIONS = [
    'cogs.aggregate_cog',
    'cogs.hephbot_cog',
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

    
if __name__ == "__main__":
    bot = SubjugationBot(command_prefix='!')
    bot.run(TOKEN)