import discord
from discord.ext import commands 
from lordsmobilemap import LordsMobileMap

import functools
import asyncio

def to_thread(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

class UtilityCog(commands.Cog):
    '''
    ユーティリティCog
    '''

    def __init__(self, bot):
        self.bot = bot
        self.lmm = LordsMobileMap(["atw"])

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong !")

    @to_thread
    def __send_code(self, tag, code):
        self.lmm.send_serial_code(tag, code)

    @commands.command()
    async def code(self, ctx, tag, code):
        '''ギフトコードをギルド全員に送る'''
        await ctx.send(f"{tag}のみんなにシリアルコード'{code}'を送るよ〜\n2分くらいかかるよ〜")
        await self.__send_code(tag, code)
        await ctx.send(f"完了しました！")

    @code.error
    async def code_error(self, ctx, error):
        await ctx.send(embed=discord.Embed(
            title="codeコマンドの使い方",
            description="!code ギルドタグ ギフトコード"
        ))

def setup(bot):
    bot.add_cog(UtilityCog(bot)) 