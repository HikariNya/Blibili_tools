import re
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.params import CommandArg

from .utils import get_uid_by_name, live_info_msg, user_info_msg, video_info_msg


user_info = on_command('查用户', priority=100, block=True)
live_info = on_command('查直播', priority=100, block=True)
video_info = on_command('查视频', priority=100, block=True)


@user_info.handle()
async def _(msg: Message = CommandArg()):
    argv = msg.extract_plain_text().replace('UID:', '').strip()
    if argv.isdigit():
        # 输入为 UID
        uid = int(argv)
    else:
        # 非 UID 则视为用户名，返回首个搜索结果
        uid = await get_uid_by_name(argv)
        if uid is None:
            await user_info.finish(f'查询失败，用户【{argv}】不存在')

    reply = await user_info_msg(uid)

    await user_info.finish(reply)


@live_info.handle()
async def _(msg: Message = CommandArg()):
    argv = msg.extract_plain_text().replace('UID:', '').strip()
    if argv.isdigit():
        # 输入为 UID
        uid = int(argv)
    else:
        # 非 UID 则视为用户名，返回首个搜索结果
        uid = await get_uid_by_name(argv)
        if uid is None:
            user_info.finish(f'查询失败，用户【{argv}】不存在')

    reply = await live_info_msg(uid)

    await live_info.finish(reply)


@video_info.handle()
async def _(msg: Message = CommandArg()):
    id = msg.extract_plain_text().strip()
    groups = re.match('^([Aa][Vv]|BV).+$', id)
    if groups is None:
        await video_info.finish('参数错误')
    
    type = groups.group(1)
    if type == 'BV':
        reply = await video_info_msg(bvid=id)
    else:
        reply = await video_info_msg(avid=id)

    await video_info.finish(reply)
