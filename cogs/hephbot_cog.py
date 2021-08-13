import discord
from discord.ext import commands 

class HephBotCog(commands.Cog):
    '''
    HephBot日本語化
    '''

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ping(self, ctx):
        await ctx.send("pong !")

def setup(bot):
    bot.add_cog(HephBotCog(bot)) 