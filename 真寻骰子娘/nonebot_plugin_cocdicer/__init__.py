from .dices import rd, help_message, st, en
from .madness import ti, li
from .investigator import Investigator
from .san_check import sc
from .cards import _cachepath, cards, cache_cards, set_handler, show_handler, sa_handler, del_handler

from nonebot import get_driver, get_bot
from nonebot.rule import Rule
from nonebot.matcher import Matcher
from nonebot.plugin import on_startswith
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent

import os

__zx_plugin_name__ = "COC骰子娘"
__plugin_usage__ = """
usage：
    COC骰子娘
    指令：
       .r 投掷指令
        .sc san check
        .st 射击命中判定
        .ti 临时疯狂症状
        .li 总结疯狂症状
        .coc coc角色作成
        .help 帮助信息
        .en 技能成长
        .set 角色卡设定
        .show 角色卡查询
        .sa 快速检定指令
        .del 删除信息

        指令详解
        .r[dah#bp] a_number [+/-]ex_number
        d：骰子设定指令，标准格式为 xdy ， x 为骰子数量 y 为骰子面数， x 为1时可以省略， y 为100时可以省略；
        a：检定指令，根据后续 a_number 设定数值检定，注意 a 必须位于 a_number 之前，且 a_number 前需使用空格隔开；
        h：暗骰指令，骰子结构将会私聊发送给该指令者；（没测试过非好友，可以的话先加好友吧）
        #：多轮投掷指令， # 后接数字即可设定多轮投掷，注意 # 后数字无需空格隔开；
        b：奖励骰指令，仅对 D100 有效，每个 b 表示一个奖励骰；
        p：惩罚骰指令，同奖励骰；
        +/-：附加计算指令，目前仅支持数字，同样无需空格隔开。

        举几个栗子：
        .r#2bba 70：两次投掷 1D100 ，附加两个奖励骰，判定值为70；
        .rah：D100暗骰，由于没有 a_number 参数，判定将被忽略；
        .ra2d8+10 70：2D8+10，由于非D100，判定将被忽略。（以上指令理论上均可随意变更顺序并嵌套使用，如果不能，就是出bug了_(:3」∠)_）
        .sc success/failure [san_number]

        *success：判定成功降低 san 值，支持 x 或 xdy 语法（ x 与 y 为数字）；
        *failure：判定失败降低 san 值，支持语法如上；
        *san_number：当前 san 值，缺省 san_number 将会自动使用保存的人物卡数据。
        .en skill_level
        
        *skill_level：需要成长的技能当前等级。
        .coc [age]

        *age：调查员年龄，缺省 age 默认年龄 20
        交互式调查员创建功能计划中
        .set [attr_name] [attr_num]

        attr_name：属性名称，例:name、名字、str、力量
        attr_num：属性值
        可以单独输入 .set 指令，骰娘将自动读取最近一次 coc 指令结果进行保存
        属性名称	缩写
            名称	name
            年龄	age
            力量	str
            体质	con
            体型	siz
            敏捷	dex
            外貌	app
            智力	int
            意志	pow
            教育	edu
            幸运	luc
            理智	san
            .show[s] [@xxx]

            .shows 查看技能指令
            查看指定调查员保存的人物卡，缺省 at 则查看自身人物卡

            *attr_name：属性名称，例:name、名字、str、力量
            .del [c|card|xxx]
            *c：清空暂存的人物卡
            *card：删除使用中的人物卡(慎用)
            *xxx：其他任意技能名
            *以上指令支持多个混合使用，多个参数使用空格隔开
""".strip()
__plugin_des__ = "COC骰子娘"
__plugin_type__ = ("群内三A游戏",)
__plugin_cmd__ = ["COC"]
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["COC"],
}
driver = get_driver()


@driver.on_startup
async def _():  # 角色卡暂存目录初始化
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(_cachepath):
        with open(_cachepath, "w", encoding="utf-8") as f:
            f.write("{}")
    cards.load()


def is_group_message() -> Rule:
    async def _is_group_message(bot: "Bot", event: "MessageEvent") -> bool:
        return True if type(event) is GroupMessageEvent else False
    return Rule(_is_group_message)


rdhelp = on_startswith(".help", priority=2, block=True)
stcommand = on_startswith(".st", priority=2, block=True)
encommand = on_startswith(".en", priority=2, block=True)
ticommand = on_startswith(".ti", priority=2, block=True)
licommand = on_startswith(".li", priority=2, block=True)
coccommand = on_startswith(".coc", priority=2, block=True)
sccommand = on_startswith(".sc", priority=2, block=True)
rdcommand = on_startswith(".r", priority=4, block=True)
setcommand = on_startswith(".set", priority=5, block=True)
showcommand = on_startswith(".show", priority=5, block=True)
sacommand = on_startswith(".sa", priority=5, block=True)
delcommand = on_startswith(".del", priority=5, block=True)


@rdhelp.handle()
async def rdhelphandler(matcher: Matcher, event: MessageEvent):
    args = str(event.get_message())[5:].strip()
    await matcher.finish(help_message(args))


@stcommand.handle()
async def stcommandhandler(matcher: Matcher):
    await matcher.finish(st())


@encommand.handle()
async def enhandler(matcher: Matcher, event: MessageEvent):
    args = str(event.get_message())[3:].strip()
    await matcher.finish(en(args))


@rdcommand.handle()
async def rdcommandhandler(event: MessageEvent):
    args = str(event.get_message())[2:].strip()
    uid = event.get_user_id()
    self_id = event.self_id
    bot = get_bot(str(self_id))
    assert isinstance(bot, Bot)
    if args and not("." in args):
        rrd = rd(args)
        if type(rrd) == str:
            await rdcommand.finish(rrd)
        elif type(rrd) == list:
            await bot.send_private_msg(user_id=uid, message=rrd[0])


@coccommand.handle()
async def cochandler(matcher: Matcher, event: MessageEvent):
    args = str(event.get_message())[4:].strip()
    try:
        args = int(args)
    except ValueError:
        args = 20
    inv = Investigator()
    await matcher.send(inv.age_change(args))
    if 15 <= args < 90:
        cache_cards.update(event, inv.__dict__, save=False)
        await matcher.finish(inv.output())


@ticommand.handle()
async def ticommandhandler(matcher: Matcher,):
    await matcher.finish(ti())


@licommand.handle()
async def licommandhandler(matcher: Matcher,):
    await matcher.finish(li())


@sccommand.handle()
async def schandler(matcher: Matcher, event: MessageEvent):
    args = str(event.get_message())[3:].strip().lower()
    await matcher.finish(sc(args, event=event))


@setcommand.handle()
async def sethandler(matcher: Matcher, event: MessageEvent):
    args = str(event.get_message())[4:].strip().lower()
    await matcher.finish(set_handler(event, args))


@showcommand.handle()
async def showhandler(matcher: Matcher, event: MessageEvent):
    args = str(event.get_message())[5:].strip().lower()
    for msg in show_handler(event, args):
        await matcher.send(msg)


@sacommand.handle()
async def sahandler(matcher: Matcher, event: MessageEvent):
    args = str(event.get_message())[3:].strip().lower()
    await matcher.finish(sa_handler(event, args))


@delcommand.handle()
async def delhandler(matcher: Matcher, event: MessageEvent):
    args = str(event.get_message())[4:].strip().lower()
    for msg in del_handler(event, args):
        await matcher.send(msg)
