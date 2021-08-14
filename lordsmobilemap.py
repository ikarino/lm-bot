from bs4 import BeautifulSoup
import requests

from datetime import datetime
import time

class LordsMobileMap:
    def __init__(self, guild_tags):
        self.guilds = {}
        for tag in guild_tags:
            self.fetch_guild_info(tag)

    def fetch_guild_info(self, guild_tag):
        resp = requests.get(f"https://lordsmobilemaps.com/en/alliance/{guild_tag}")
        soup = BeautifulSoup(resp.text, 'html.parser')
        playernames = soup.select('.tobtab2col div:nth-of-type(n+2) div:nth-of-type(2) a')
        powers = soup.select('.tobtab2col div:nth-of-type(n+5) div:nth-of-type(5)')
        self.guilds[guild_tag] = {
            "updated": datetime.now(),
            "data": [
                {
                    "name": playername.text,
                    "power": int(power.text.replace(".", "")),
                }
                for playername, power in zip(playernames, powers)
            ],
        }

    def send_serial_code(self, guild_tag, code):
        if guild_tag not in self.guilds:
            self.fetch_guild_info(guild_tag)
        delta = datetime.now() - self.guilds[guild_tag]['updated']
        if delta.days > 1:
            self.fetch_guild_info(guild_tag)
        for p in self.guilds[guild_tag]['data']:
            requests.post('https://lordsmobile.igg.com/project/gifts/ajax.php?game_id=1051029902', data={'ac':'get_gifts', 'type':'1', 'iggid':'0', 'charname': p['name'], 'cdkey': code, 'lang': 'en'})
            time.sleep(1)

        


if __name__ == "__main__":
    l = LordsMobileMap(["atw"])
    l.send_serial_code("atw", "hello")
    print("yes")