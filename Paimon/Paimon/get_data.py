import datetime
import re

from littlepaimon_utils import aiorequests
from nonebot import logger

from .utils.decorator import cache


# 获取签到奖励列表
async def get_sign_list():
    url = 'https://api-takumi.mihoyo.com/event/bbs_sign_reward/home'
    headers = {
        'x-rpc-app_version': '2.11.1',
        'User-Agent':        'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 ('
                             'KHTML, like Gecko) miHoYoBBS/2.11.1',
        'x-rpc-client_type': '5',
        'Referer':           'https://webstatic.mihoyo.com/'
    }
    params = {
        'act_id': 'e202009291139501'
    }
    resp = await aiorequests.get(url=url, headers=headers, params=params)
    data = resp.json()
    return data


async def get_enka_data(uid):
    try:
        url = f'https://enka.network/u/{uid}/__data.json'
        resp = await aiorequests.get(url=url, headers={'User-Agent': 'LittlePaimon/2.0'}, follow_redirects=True)
        data = resp.json()
        return data
    except Exception:
        url = f'https://enka.microgg.cn/u/{uid}/__data.json'
        resp = await aiorequests.get(url=url, headers={'User-Agent': 'LittlePaimon/2.0'}, follow_redirects=True)
        data = resp.json()
        return data


async def get_stoken_by_login_ticket(loginticket, mys_id):
    req = await aiorequests.get(url='https://api-takumi.mihoyo.com/auth/api/getMultiTokenByLoginTicket',
                                params={
                                    'login_ticket': loginticket,
                                    'token_types':  '3',
                                    'uid':          mys_id
                                })
    return req.json()
