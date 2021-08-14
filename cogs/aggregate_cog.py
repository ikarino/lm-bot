from discord import Embed, File
from discord.ext import commands # Bot Commands Frameworkのインポート
from ocr import (
    might_ranking_imgs2players,
    gift_img2gifts
)
from datetime import datetime

CHANNEL_AGGREGATES = [
    875307673782976563,  # 860 server
    868271217017237530,  # push server
]

class AggregateCog(commands.Cog):
    '''
    討伐回データ集計関係
    '''
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def player(self, ctx):
        '''
        パワーランキング画像から参加者一覧を上書きする
        '''
        if ctx.channel.id not in CHANNEL_AGGREGATES:
            return 
        msg = ctx.message
        name = msg.author # msg.nick if msg.nick else msg.name
        if not msg.attachments:
            await ctx.send("画像が添付されてないよ〜\nパワーランキング画像をplayerコマンドと一緒に添付して下さい。")
            return
        urls = [att.url for att in msg.attachments]
        await ctx.send(f'パワーランキング画像を受け取りました！参加者リストを作成中です')

        players = might_ranking_imgs2players(urls=urls)
        if players:
            embed = Embed(
                title="参加者リスト",
                color=0xff0000,
                description="\n".join([p['player_name'] for p in players])
            )
            self.bot.db.set_current_player_names(players)
            await ctx.send(embed=embed)
        else:
            await ctx.send("参加者が1人も見つかりませんでした。")

    @commands.command()
    async def agift(self, ctx):
        '''
        ギフト画像からギフト一覧に追加する
        '''
        if ctx.channel.id not in CHANNEL_AGGREGATES:
            return 
        msg = ctx.message
        if not msg.attachments:
            await ctx.send("画像が添付されてないよ〜\nギフト画像をagiftコマンドと一緒に添付して下さい。")
            return
        urls = [att.url for att in msg.attachments]
        await ctx.send(f'ギフト画像を受け取りました！追加中です')

        gifts = gift_img2gifts(urls=urls)
        if gifts:
            self.bot.db.append_current_gifts(gifts)
            await ctx.send(f"{len(gifts)}個のギフトを追加しました！")
        else:
            await ctx.send(f"画像からギフトを見つけられませんでした。")

    @commands.command()
    async def rgift(self, ctx):
        '''
        ギフト一覧を削除する
        '''
        if ctx.channel.id not in CHANNEL_AGGREGATES:
            return 
        self.bot.db.remove_gifts()
        await ctx.send("ギフト一覧を削除しました")

    @commands.command()
    async def sgift(self, ctx):
        '''
        ギフトのサマリーを表示
        '''
        if ctx.channel.id not in CHANNEL_AGGREGATES:
            return 
        gifts = self.bot.db.get_current_gifts()
        embed = Embed(
            title="ギフトサマリー",
            color=0x00ff00,
        )

        ranks = [0]*5
        for g in gifts:
            ranks[g['rank']-1] += 1
        for r in range(5):
            embed.add_field(
                name=f"**Lv.{r+1}**",
                value=ranks[r],
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command()
    async def lplayer(self, ctx):
        '''
        現在の参加者リストを表示
        '''
        if ctx.channel.id not in CHANNEL_AGGREGATES:
            return 
        players = self.bot.db.get_current_players()
        embed = Embed(
            title="参加者リスト",
            color=0x00ff00,
            description="\n".join(players)
        )
        await ctx.send(embed=embed)

    @commands.command()
    async def save(self, ctx):
        '''
        参加者リストとギフト一覧を保存する
        '''
        if ctx.channel.id not in CHANNEL_AGGREGATES:
            return 
        key = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.bot.db.save_as(key)
        await ctx.send(f"{key}という名前で保存しました！")

    @commands.command()
    async def result(self, ctx):
        '''
        集計結果を表示
        '''
        if ctx.channel.id not in CHANNEL_AGGREGATES:
            return
        await ctx.send("集計結果を表示します。少々お待ち下さい。")
        result = self.bot.db.get_result()
        embed = Embed(
            title="集計結果",
            color=0x00ff00,
        )
        csv = "name,common,Uncommon,Rare,Epic,Legendary\n"
        description = ''
        for p, gifts in result.items():
            if p == "Error":
                continue
            description += f'**{p}** {gifts}\n'
            csv += f"{p},{','.join(map(str, gifts))}\n"
        embed = Embed(
            title=f"集計結果",
            color=0x00ff00,
            description=description
        )
        if "Error" not in result:
            with open("result.csv", 'w') as f:
                f.write(csv)
            await ctx.send(embed=embed, file=File("result.csv"))
            return

        await ctx.send(embed=embed)
        csv += '\n\nError gifts:\nname,rank\n'
        for e in result["Error"]:
            csv += f"{e['player_name']},{e['rank']}\n"
        embed = Embed(
            title="読み取りエラーまたは参加者リスト外",
            color=0xff0000,
            description="\n".join(
                f"{e['player_name']}(lv{e['rank']})"
                for e in result["Error"]
            )
        )
        with open("result.csv", 'w') as f:
            f.write(csv)
        await ctx.send(embed=embed, file=File("result.csv"))
 

def setup(bot):
    bot.add_cog(AggregateCog(bot)) 