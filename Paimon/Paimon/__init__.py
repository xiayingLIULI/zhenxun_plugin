import contextlib
import datetime
import random
import re
from asyncio import sleep
from collections import defaultdict

from littlepaimon_utils.tools import FreqLimiter
from nonebot import on_command, require, logger, get_bot
from nonebot.adapters.onebot.v11 import MessageEvent, Message, Bot, MessageSegment
from nonebot.params import CommandArg, Arg
from nonebot.permission import SUPERUSER
from nonebot.plugin import PluginMetadata
from nonebot.rule import to_me
from nonebot.typing import T_State
from .utils.db_util import Genshin
from .draw_role_card import draw_role_card
from .get_data import get_enka_data
from .utils.alias_handler import get_match_alias
from .utils.decorator import exception_handler
from .utils.enka_util import PlayerInfo
from .utils.message_util import MessageBuild as MsgBd
from .utils.message_util import get_uid_in_msg, uid_userId_to_dict, replace_all, transform_uid, get_message_id

__zx_plugin_name__ = "原神角色面板"
__plugin_usage__ = """
usage：
    查询橱窗内角色的具体面板
    指令：
        [udi/更新角色信息/更新角色面板/更新玩家信息 uid]更新游戏内展柜8个角色的面板信息
        [ysd/角色详情/角色信息/角色面板 角色名 uid]查看指定角色的详细面板信息
""".strip()
__plugin_des__ = "查询橱窗内角色的面板"
__plugin_cmd__ = ["udi/更新角色信息/更新角色面板/更新玩家信息 uid"]
__plugin_type__ = ("原神相关", )
__plugin_version__ = 0.1
__plugin_author__ = "琉璃"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["原神角色面板"],
}

update_info = on_command('udi', aliases={'更新角色信息', '更新角色面板', '更新玩家信息'}, priority=6, block=True)
role_info = on_command('角色面板', aliases={'角色详情', '角色信息', 'ysd'}, block=True, priority=7)

ud_lmt = FreqLimiter(180)
ud_p_lmt = FreqLimiter(15)


@update_info.handle()
async def _(event: MessageEvent, state: T_State, msg: Message = CommandArg()):
    if uid := re.search(r'(?P<uid>(1|2|5|8)\d{8})', msg.extract_plain_text().strip()):
        state['uid'] = uid.group('uid')
    else:
        if user := next((msg_seg.data['qq'] for msg_seg in msg if msg_seg.type == "at"), ''):
            uid = await Genshin.get_last_query(str(user))
        else:
            uid = await Genshin.get_last_query(str(event.user_id))
        if uid:
            state['uid'] = uid
    if 'uid' in state and not ud_lmt.check(state['uid']):
        await update_info.finish(f'每个uid每3分钟才能更新一次信息，请稍等一下吧~(剩余{ud_lmt.left_time(state["uid"])}秒)')
    if not ud_p_lmt.check(get_message_id(event)):
        await update_info.finish(f'每个会话每15秒才能更新一次信息，请稍等一下吧~(剩余{ud_lmt.left_time(get_message_id(event))}秒)')


@update_info.got('uid', prompt='请把要更新的uid给ATRI哦~')
@exception_handler()
async def _(event: MessageEvent, uid: Message = Arg('uid')):
    uid = transform_uid(uid)
    if not uid:
        await update_info.finish('这好像不是一个正确的uid哦~，请检查一下', at_sender=True)
    await Genshin.update_last_query(str(event.user_id), uid)

    await update_info.send('ATRI开始更新信息~请稍等哦~')
    enka_data = await get_enka_data(uid)
    if not enka_data:
        await update_info.finish('ATRI没有获取到该uid的信息哦，可能是enka接口服务出现问题，稍候再试吧~')
    ud_lmt.start_cd(uid, 180)
    ud_lmt.start_cd(get_message_id(event), 15)
    player_info = PlayerInfo(uid)
    player_info.set_player(enka_data['playerInfo'])
    if 'avatarInfoList' not in enka_data:
        player_info.save()
        await update_info.finish('你未在游戏中打开角色展柜，ATRI查不到~请打开5分钟后再试~')
    else:
        for role in enka_data['avatarInfoList']:
            player_info.set_role(role)
        player_info.save()
        role_list = list(player_info.get_update_roles_list().keys())
        await update_info.finish(f'uid{uid}更新完成~本次更新的角色有：\n' + ' '.join(role_list))


@role_info.handle()
async def _(event: MessageEvent, state: T_State, msg: Message = CommandArg()):
    if uid := re.search(r'(?P<uid>(1|2|5|8)\d{8})', msg.extract_plain_text().strip()):
        state['uid'] = uid.group('uid')
        await Genshin.update_last_query(str(event.user_id), uid.group('uid'))
    else:
        user = ''
        for msg_seg in msg:
            if msg_seg.type == "at":
                user = msg_seg.data['qq']
        if user:
            uid = await Genshin.get_last_query(str(user))
        else:
            uid = await Genshin.get_last_query(str(event.user_id))
        if uid:
            state['uid'] = uid
    msg = msg.extract_plain_text().replace(state['uid'] if 'uid' in state else 'ysd', '').strip()
    if not msg:
        await role_info.finish('请把要查询角色名给ATRI哦~')
    if msg.startswith(('a', '全部', '所有', '查看')):
        state['role'] = 'all'
    else:
        match_alias = get_match_alias(msg, 'roles', True)
        if match_alias:
            state['role'] = match_alias if isinstance(match_alias, str) else tuple(match_alias.keys())[0]
        else:
            await role_info.finish(MsgBd.Text(f'哪有名为{msg}的角色啊，别拿ATRI开玩笑!'))


@role_info.got('uid', prompt='请把要查询的uid给ATRI哦~')
@exception_handler()
async def _(event: MessageEvent, state: T_State):
    uid = transform_uid(state['uid'])
    if uid:
        state['uid'] = uid
    else:
        await role_info.finish('这个uid不正确哦~，请检查一下', at_sender=True)
    uid = await Genshin.get_last_query(str(event.user_id))
    role = state['role']
    player_info = PlayerInfo(uid)
    roles_list = player_info.get_roles_list()
    if role == 'all':
        if not roles_list:
            await role_info.finish('你在ATRI这里没有角色面板信息哦，先用 更新角色信息 命令获取吧~', at_sender=True)
        res = '目前已获取的角色面板有：\n'
        for r in roles_list:
            res += r
            res += ' ' if (roles_list.index(r) + 1) % 4 else '\n'
        await role_info.finish(res, at_sender=True)
    if role not in roles_list:
        await role_info.finish(MsgBd.Text(f'ATRI还没有你{role}的信息哦，先用 更新角色信息 命令更新吧~'), at_sender=True)
    else:
        role_data = player_info.get_roles_info(role)
        img = await draw_role_card(uid, role_data)
        await role_info.finish(img)





