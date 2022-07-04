import json
import urllib3
from nonebot import on_command
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GROUP, GROUP_OWNER, GROUP_ADMIN, Message, GroupMessageEvent, \
    MessageSegment
from nonebot.params import CommandArg
from nonebot.matcher import Matcher

__zx_plugin_name__ = "刷步数"
__plugin_usage__ = """
usage：
    小米运动刷微信步数
    指令：
        步数 [小米运动账号] [小米运动密码] [步数]
"""
__plugin_des__ = "步数"
__plugin_type__ = ("常规插件",)
__plugin_cmd__ = ["步数"]
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["步数"],
}
main = on_command("步数", priority=5, block=True)


@main.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    msg = arg.extract_plain_text().strip().split()
    try:
        mobile = int(msg[0])
    except:
        await main.send("请输入小米运动账号")
        return
    if len(msg) >= 2:
        password = msg[1]
    else:
        await main.send("请输入小米运动密码")
        return
    if len(msg) == 3:
        step = msg[2]
    else:
        await main.send("请输入步数")
        return
    url = f'https://api.kit9.cn/api/milletmotion/?mobile={mobile}&password={password}&step={step}'
    r = urllib3.PoolManager().request('GET', url)
    hjson = json.loads(r.data.decode())
    content_code = hjson["code"]
    if content_code == 200:
        text_url = hjson["data"]["state"]
        out_msg = MessageSegment.text(text_url)
        await main.finish(message=out_msg, at_sender=True)
    else:
        text_url1 = hjson["data"]
        out_msg = MessageSegment.text(text_url1)
        await main.finish(message=out_msg, at_sender=True)
