from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import ReadOperationResult
from msrest.authentication import CognitiveServicesCredentials
import coloredlogs
from dotenv import load_dotenv

from pprint import pprint
from logging import getLogger
import os
import time
import pickle

load_dotenv(override=True)
logger = getLogger(__name__)
coloredlogs.install(level="DEBUG")


BOX_RANKS = {
    "[コモン]": 1,
    "[アンコモン]": 2,
    "[レア]": 3,
    "[エピック]": 4,
    "[レジェンド]": 5
}

class OCRError(Exception):
    pass

SUBSCRIPTION_KEY = os.getenv('SUBSCRIPTION_KEY')
ENDPOINT = os.getenv('ENDPOINT')
COMPUTERVISION_CLIENT = ComputerVisionClient(ENDPOINT, CognitiveServicesCredentials(SUBSCRIPTION_KEY))

def __imgurl2readresult(imgurl: str, fname=None) -> ReadOperationResult:
    '''
    Free レベルでは、要求レートは 1 分あたり 20 回の呼び出しに制限されます。
    '''
    read_response = COMPUTERVISION_CLIENT.read(imgurl,  raw=True)

    read_operation_location = read_response.headers["Operation-Location"]
    # Grab the ID from the URL
    operation_id = read_operation_location.split("/")[-1]
    
    # Call the "GET" API and wait for it to retrieve the results 
    while True:
        read_result = COMPUTERVISION_CLIENT.get_read_result(operation_id)
        if read_result.status == "failed":
            raise OCRError("Azure returned: failed")
        elif read_result.status == "succeeded":
            break
        time.sleep(1)
    
    if fname:
        with open(fname, "wb")  as f:
            pickle.dump(read_result, f)
    return read_result

def __might_ranking_img2players(imgurl=None, read_result=None) -> list:
    if imgurl:
        read_result = __imgurl2readresult(imgurl)
    elif read_result:
        read_result = read_result
    else:
        raise OCRError("invalid input for might_ranking_img2players")
    assert len(read_result.analyze_result.read_results) == 1
    result = read_result.analyze_result.read_results[0]
    # 画像サイズで倍率設定
    width = result.width
    height = result.height
    logger.debug(f"width: {width}, height: {height}, ratio: {width/height:.2f}")
    def magnify(bbox):
        # TODO
        # 拡大縮小してiPhone-SE2の解像度に合わせる
        # width: 1334.0, height: 750.0
        w_ratio = 1334/width
        h_ratio = 750/height
        bbox = (
            w_ratio*min(bbox[0], bbox[6]),  # xmin
            h_ratio*min(bbox[1], bbox[3]),  # ymin
            w_ratio*max(bbox[2], bbox[4]),  # xmax
            h_ratio*max(bbox[5], bbox[7]),  # ymax
        )
        return bbox

    players = []
    player = {}
    flag = "rank"
    for line in result.lines:
        bbox = magnify(line.bounding_box)
        bwidth = bbox[2] - bbox[0]
        mheight = (bbox[1]+bbox[3])/2
        # 範囲外（上側、右半分）の場合はスキップ
        if bbox[1] < 200 or bbox[0] > 1334/2:
            continue
        text = line.text
        logger.info(f"{text:20s}@{bbox}")
        if flag == "rank" and bwidth < 50 and bbox[0] < 200:
            try:
                rank = int(text)
                player['rank'] = rank
                flag = "player_name"
            except ValueError:
                continue
        elif flag == "player_name" and bwidth > 50:
            player_name = text
            player['player_name'] = player_name
            players.append(player)
            player = {}
            flag = "rank"
    return players


def might_ranking_imgs2players(urls=None, read_results=None) -> list:
    started = time.time()
    players = []
    if urls:
        for url in urls:
            players += __might_ranking_img2players(imgurl=url)
    elif read_results:
        for read_result in read_results:
            players += __might_ranking_img2players(read_result=read_result)
    players = sorted(players, key=lambda x: x['rank'])

    # 重複を除去
    __players = []
    __ranks = []
    for player in players:
        rank = player['rank']
        if rank in __ranks:
            continue
        __players.append(player)
        __ranks.append(rank)

    # API呼び出し上限処理
    if urls:
        sec_elapsed = time.time() - started
        sec_to_sleep = len(urls) * 3 - sec_elapsed # 1分で20回呼び出し可能
        if sec_to_sleep > 0:
            logger.warning(f"API limit, sleeping {sec_to_sleep:.2f}sec")
            time.sleep(sec_to_sleep)
    return __players

def __gift_img2gift(imgurl=None, read_result=None) -> list:
    if imgurl:
        read_result = __imgurl2readresult(imgurl)
    elif read_result:
        read_result = read_result
    else:
        raise OCRError("invalid input for gift_img2gift")
    assert len(read_result.analyze_result.read_results) == 1
    result = read_result.analyze_result.read_results[0]

    def magnify(bbox):
        # TODO
        # 拡大縮小してiPhone-SE2の解像度に合わせる

        bbox = (
            min(bbox[0], bbox[6]),  # xmin
            min(bbox[1], bbox[3]),  # ymin
            max(bbox[2], bbox[4]),  # xmax
            max(bbox[5], bbox[7]),  # ymax
        )
        return bbox

    rank = None
    gifts = []
    for line in result.lines:
        bbox = magnify(line.bounding_box)
        text = line.text
        # print(f"{text:20s} @{bbox}")
        for __rank in BOX_RANKS:
            if __rank in text:
                if rank != None:
                    raise OCRError(f"誰からのギフトか分かりませんでした: {imgurl}")
                rank = BOX_RANKS[__rank]
        if "からのギフト" in text:
            if rank == None:
                raise OCRError(f"ギフトのランクが読み取れませんでした。: {imgurl}")
            player_name = text.replace("からのギフト", "")
            gifts.append({
                'player_name': player_name,
                "rank": rank
            })
            rank = None
    return gifts

def gift_img2gifts(urls=None, read_results=None) -> list:
    started = time.time()
    gifts = []
    if urls:
        for url in urls:
            gifts += __gift_img2gift(imgurl=url)
    elif read_results:
        for read_result in read_results:
            gifts += __gift_img2gift(read_result=read_result)

    # API呼び出し上限処理
    if urls:
        sec_elapsed = time.time() - started
        sec_to_sleep = len(urls) * 3 - sec_elapsed # 1分で20回呼び出し可能
        if sec_to_sleep > 0:
            logger.warning(f"API limit, sleeping {sec_to_sleep:.2f}sec")
            time.sleep(sec_to_sleep)
    return gifts


def test_might_ranking():
    # url = "https://cdn.discordapp.com/attachments/874265851698745384/875207943803531264/image0.png"
    # __imgurl2readresult(url, "might_ranking_1.pickle")
    url = 'https://cdn.discordapp.com/attachments/874265851698745384/875207944155836436/image1.png'
    url = 'https://cdn.discordapp.com/attachments/868271217017237530/875619108413124618/sc.png'
    pprint(__might_ranking_img2players(imgurl=url))
    # with open("might_ranking_1.pickle", "rb") as f:
    #     r1 = pickle.load(f)
    # with open("might_ranking_2.pickle", "rb") as f:
    #     r2 = pickle.load(f)
    # 
    # might_ranking_imgs2players(read_results=[r1, r2])

if __name__ == "__main__":
    # test_might_ranking()
    # url = 'https://cdn.discordapp.com/attachments/874265851698745384/875235374551678976/image0.png'
    # __imgurl2readresult(url, fname="gift_1.pickle")
    # url = 'https://cdn.discordapp.com/attachments/874265851698745384/875236013813936209/image0.png'
    # __imgurl2readresult(url, fname="gift_2.pickle")
    with open("gift_1.pickle", "rb") as f:
        r1 = pickle.load(f)
    with open("gift_2.pickle", "rb") as f:
        r2 = pickle.load(f)
    print(gift_img2gifts(read_results=[r1, r2]))