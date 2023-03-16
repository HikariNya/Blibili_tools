import re
from bilibili_api.exceptions import ArgsException, NetworkException, ResponseCodeException
from bilibili_api.search import search_by_type, SearchObjectType
from bilibili_api.user import User
from bilibili_api.video import Video
from nonebot import logger
from nonebot.adapters.onebot.v11 import Message, MessageSegment


async def get_uid_by_name(name: str) -> int or None:
    try:
        data = await search_by_type(name, SearchObjectType.USER)
    except (NetworkException, ResponseCodeException) as e:
        logger.exception(e)
        return None
    
    if data['numResults'] == 0:
        return None

    user = data['result'][0]
    uid = user['mid']
    return uid


async def user_info_msg(uid: int) -> str or Message:
    user = User(uid)
    try:
        info = await user.get_user_info()           # 用户信息
        relation = await user.get_relation_info()   # 关注信息
    except ResponseCodeException as e:
        if e.code == -404:
            return f'用户（UID:{uid}）不存在'
        else:
            logger.exception(e)
            return '查询失败，请等待5分钟后重试'
    except NetworkException as e:
        logger.exception(e)
        return '查询失败，请等待5分钟后重试'

    mid, name, face, sign = info['mid'], info['name'], info['face'], info['sign']
    following, follower = relation['following'], relation['follower']

    text = f'\nUID：{mid}\n' \
           f'昵称：{name}\n' \
           f'关注数：{following}\n' \
           f'粉丝数：{follower}\n' \
           f'个性签名：{sign}\n' \
           f'主页：https://space.bilibili.com/{mid}'

    return Message([
        MessageSegment.image(face),
        MessageSegment.text(text)
    ])


async def live_info_msg(uid: int) -> str or Message:
    user = User(uid)
    try:
        info = await user.get_live_info()   # 直播信息无独立 api，与 get_user_info() 使用的 api 一致
    except ResponseCodeException as e:
        if e.code == -404:
            return f'用户（UID:{uid}）不存在'
        else:
            logger.exception(e)
            return '查询失败，请等待5分钟后重试'
    except NetworkException as e:
        logger.exception(e)
        return '查询失败，请等待5分钟后重试'

    # 直播信息只能通过用户信息获取
    mid, name, live_room = info['mid'], info['name'], info['live_room']

    if live_room is None or live_room['roomStatus'] == 0:
        return f'用户【{name}】暂未开通直播间'

    status, url, title, cover, roomid = live_room['liveStatus'], live_room['url'], live_room['title'], live_room['cover'], live_room['roomid']
    url = re.match('^(.*)\?.*$', url).group(1)  # 清除无用参数

    text = f'\n{name}\n' \
           f'UID：{mid}\n' \
           f'直播间号：{roomid}\n' \
           f'状态：{"正在直播" if status == 1 else "未开播"}\n' \
           f'标题：{title}\n' \
           f'地址：{url}'

    return Message([
        MessageSegment.image(cover),
        MessageSegment.text(text)
    ])


def num2text(num: int or float) -> str:
    if num < 10000:
        return str(num)
    elif num < 100000000:
        return f'{num / 10000:.1f}万'
    else:
        return f'{num / 100000000:.1f}亿'


async def video_info_msg(bvid: str = None, avid: str = None) -> str or Message:
    if bvid is not None:
        try:
            video = Video(bvid=bvid)
        except ArgsException as e:
            return e.msg
        except KeyError:
            return 'BV号错误，请检查BV号是否正确'
    elif avid is not None:
        aid = avid[2:]
        try:
            aid = int(aid)
            video = Video(aid=aid)
        except ValueError:
            return 'av号格式错误'
        except ArgsException as e:
            return e.msg
    else:
        raise Exception('expected 1 argument at least, got 0')
    
    try:
        info = await video.get_info()
    except ResponseCodeException as e:
        if e.code == -403:
            return '权限不足，暂时无法查看该视频'
        elif e.code == -404:
            return f'找不到该视频，请检查{"BV" if bvid is not None else "av"}号是否正确'
        elif e.code == 62002:
            return '该视频不可见'
        elif e.code == 62004:
            return '该稿件审核中'
        else:
            logger.exception(e)
            return '查询失败，请等待5分钟后重试'
    except NetworkException as e:
        logger.exception(e)
        return '查询失败，请等待5分钟后重试'

    pic, title, desc, owner_name, stat_view, stat_danmaku = info['pic'], info['title'], info['desc'], info['owner']['name'], info['stat']['view'], info['stat']['danmaku']

    text = f'\n{title}\n' \
           f'UP主：{owner_name}\n' \
           f'简介：{desc if len(desc) <= 150 else desc[:150] + "……"}\n' \
           f'{num2text(stat_view)}播放 {num2text(stat_danmaku)}弹幕\n' \
           f'https://www.bilibili.com/video/{bvid if bvid is not None else avid}'

    return Message([
        MessageSegment.image(pic),
        MessageSegment.text(text)
    ])
