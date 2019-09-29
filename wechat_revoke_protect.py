# -*- coding: utf-8 -*-
"""
Project: HelloWorldPython
Creator: DoubleThunder
Create time: 2019-09-28 12:18
Introduction: 微信防撤回功能
微信防撤回功能。
（先确定你的微信号能登录网页版微信）
实现功能：
1. 监听所有的消息（好友，群组）保存于字典中，非文字消息，保存文件到缓存文件夹。
2. 监听系统公告通知，如果有好友撤回消息。而从字典中取出数据，发送到你的『文件传输助手』中。
    如果你将 is_auto_repost = True，撤回的消息会即可发送给好友或群组。

此项目需要的库有：itchat，apscheduler

"""
import itchat
from itchat.content import *
import os
import time
import shutil
import re

# import json
# import pysnooper

from apscheduler.schedulers.background import BackgroundScheduler

# 文件临时存储地址
rec_tmp_dir = os.path.join(os.getcwd(), 'tmp', 'revoke')
is_auto_repost = True  # 是否转发给撤回的人或者群
CLEAN_CACHE_INTERVAL_MINUTES = 5  # 心跳时间间隔（分钟）


# 存储数据的字典
rec_msg_dict = {}

# 判断消息是否为撤回消息公告(包括了简体|繁体|英文)
revoke_msg_compile = r'^<sysmsg type="revokemsg"><revokemsg><session>(.*?)<\/session>' \
                     r'<oldmsgid>.*?<\/oldmsgid><msgid>(.*?)<\/msgid>.*?"(.*?)"\s(?:撤回了一条消息|已回收一條訊息|recalled a message)'


# 用于定时清理缓存数据
scheduler = BackgroundScheduler()

# 消息类型的中文名称，与转发标识
content_type_dict = {
    'Text': {'name': '文字', 'code': '@msg@'},
    'Map': {'name': '地图', 'code': '@msg@'},
    'Card': {'name': '名片', 'code': '@msg@'},
    'Note': {'name': '系统消息', 'code': '@msg@'},
    'Sharing': {'name': '分享', 'code': '@msg@'},
    'Picture': {'name': '图片', 'code': '@img@'},
    'Recording': {'name': '语音', 'code': '@fil@'},
    'Attachment': {'name': '附件', 'code': '@fil@'},
    'Video': {'name': '视频', 'code': '@vid@'},
    'Friends': {'name': '好友邀请', 'code': '@msg@'},
    'System': {'name': '系统', 'code': '@msg@'}
}



@itchat.msg_register([TEXT, PICTURE, RECORDING, ATTACHMENT, VIDEO, CARD, MAP, SHARING], isFriendChat=True)
def handle_friend_msg(msg):
    """
    # 好友信息监听
   :param msg:
   :return:
   """
    # print(json.dumps(msg, ensure_ascii=False))
    msg_id = msg['MsgId']  # 消息 id
    msg_from_name = msg['User']['NickName']  # 用户的昵称
    msg_from_uid = msg['FromUserName']  # 用户的昵称

    msg_content = ''
    # 收到信息的时间
    msg_time_rec = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    msg_create_time = msg['CreateTime']
    msg_type = msg['Type']

    if msg_type == 'Text':
        msg_content = msg['Content']

    elif msg_type in ('Picture', 'Recording', 'Video', 'Attachment'):
        msg_content = os.path.join(rec_tmp_dir, msg['FileName'])
        msg['Text'](msg_content)  # 保存数据至此路径

    # 名片，是无法用 itchat 发送的
    elif msg_type == 'Card':
        recommendInfo = msg['RecommendInfo']
        nickname = recommendInfo['NickName']
        sex = '男' if recommendInfo['Sex'] == 1 else '女'
        msg_content = '名片：{nickname},性别：{sex}'.format(nickname=nickname, sex=sex)

    # 地图与分享无法用 itchat 实现发送
    elif msg_type in ('Map', 'Sharing'):
        msg_content = msg['Url']

    rec_msg_dict.update({
        msg_id: {
            'is_group': False,
            'msg_from_name': msg_from_name,
            'msg_from_uid': msg_from_uid,
            'msg_time_rec': msg_time_rec,
            'msg_create_time': msg_create_time,
            'msg_type': msg_type,
            'msg_content': msg_content
        }
    })
    # print(msg)



@itchat.msg_register([TEXT, PICTURE, RECORDING, ATTACHMENT, VIDEO, CARD, MAP, SHARING], isGroupChat=True)
def information(msg):
    """
    # 群聊信息监听
    :param msg:
    :return:
    """
    # print(json.dumps(msg, ensure_ascii=False))
    msg_id = msg['MsgId']  # 消息id
    msg_from_name = msg['ActualNickName']  # 发送者名称
    msg_from_uid = msg['ActualUserName']  # 发送者的id

    msg_group_uid = msg['User']['UserName']  # 群uid
    msg_group_name = msg['User']['NickName']  # 群名称

    msg_content = ''
    # 收到信息的时间
    msg_time_rec = time.time()
    msg_create_time = msg['CreateTime']
    msg_type = msg['Type']

    if msg_type == 'Text':
        msg_content = msg['Content']
    elif msg_type in ('Picture', 'Recording', 'Video', 'Attachment'):
        msg_content = os.path.join(rec_tmp_dir, msg['FileName'])
        msg['Text'](msg_content)  # 保存数据至此路径

    # 名片，是无法用 itchat 发送的
    elif msg_type == 'Card':
        recommendInfo = msg['RecommendInfo']
        nickname = recommendInfo['NickName']
        sex = '男' if recommendInfo['Sex'] == 1 else '女'
        msg_content = '名片：{nickname},性别：{sex}'.format(nickname=nickname, sex=sex)

    # 地图与分享无法用 itchat 实现发送
    elif msg_type in ('Map', 'Sharing'):
        msg_content = msg['Url']

    rec_msg_dict.update({
        msg_id: {
            'is_group': True,
            'msg_group_uid': msg_group_uid,
            'msg_group_name': msg_group_name,
            'msg_from_name': msg_from_name,
            'msg_from_uid': msg_from_uid,
            'msg_time_rec': msg_time_rec,
            'msg_create_time': msg_create_time,
            'msg_type': msg_type,
            'msg_content': msg_content
        }
    })

    # print(msg)
    # print(json.dumps(msg, ensure_ascii=False))


@itchat.msg_register([NOTE], isFriendChat=True, isGroupChat=True)
def revoke_msg(msg):
    """
    监听系统公告。
    :param msg:
    :return:
    """
    content = msg['Content']
    # print(json.dumps(msg, ensure_ascii=False))
    infos = re.findall(revoke_msg_compile, content)
    if infos:
        _, old_msg_id, nickname = infos[0]
        old_msg = rec_msg_dict.get(old_msg_id, {})
        if old_msg:
            # 判断文msg_content是否存在，不存在说明可能是
            msg_type = old_msg.get('msg_type')
            msg_content = old_msg.get('msg_content')
            msg_from_name = old_msg.get('msg_from_name')
            if not msg_type or not msg_content:
                return
            is_group = old_msg.get('is_group')
            send_msg = ''
            if is_group:
                uid = old_msg.get('msg_group_uid')
                msg_type_name = content_type_dict.get(msg_type).get('name')  # 类型的中文名称
                send_msg = '群『{msg_group_name}』里的『{msg_from_name}』撤回了一条{msg_type_name}信息'.format(
                    msg_group_name=old_msg.get('msg_group_name'),
                    msg_from_name=msg_from_name,
                    msg_type_name=msg_type_name,
                )
            else:
                uid = old_msg.get('msg_from_uid')
                msg_type_name = content_type_dict.get(msg_type).get('name')  # 类型的中文名称
                send_msg = '『{msg_from_name}』撤回了一条{msg_type_name}信息'.format(
                    msg_from_name=msg_from_name,
                    msg_type_name=msg_type_name,
                )
            print(send_msg, msg_content)
            send_revoke_msg(send_msg, uid, is_auto_repost=is_auto_repost)
            send_revoke_msg(msg_content, uid, msg_type, is_auto_repost)


def send_revoke_msg(msg_content, toUserName='filehelper', msg_type='Text', is_auto_repost=False):
    """
    :param msg_content: 消息内容
    :param toUserName: 用户uid
    :param msg_type: 消息类型
    :param is_auto_repost: 是否给用户发送撤回消息。
    :return:
    """
    # 消息类型不能为空，默认为文字消息
    if not msg_type or msg_type not in content_type_dict:
        msg_type = 'Text'
    #
    at_ = content_type_dict.get(msg_type).get('code')
    msg_content = '{}{}'.format(at_, msg_content)

    # 发送给文件传输助手
    itchat.send(msg_content, 'filehelper')
    if is_auto_repost and toUserName != 'filehelper':
        itchat.send(msg_content, toUserName) #发送给好友，或者群组。


def clear_cache():
    """
    # 每隔五分钟执行一次清理任务,如果有创建时间超过2分钟(120s)的记录，删除。
    # 非文本的话，连文件也删除
    :return:
    """
    cur_time = time.time()  # 当前时间
    for key, value in list(rec_msg_dict.items()):
        if cur_time - value.get('msg_time_rec') > 120:
            if value.get('msg_type') not in ('Text', 'Map', 'Card', 'Sharing'):
                file_path = value.get('msg_content')
                # print(file_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            rec_msg_dict.pop(key)



def after_logout():
    """
    退出登录时，清理数据库，并关闭定时任务
    :return:
    """
    if scheduler and scheduler.get_jobs():
        scheduler.shutdown(wait=False)
    shutil.rmtree(rec_tmp_dir)


def before_login():
    """
    登录时，开启定时清理缓存
    :return:
    """

    itchat.get_friends(update=True) # 更新用户好友状态
    itchat.get_chatrooms(update=True) # 更新用户群组状态

    # 如果还存在定时任务，先关闭。
    if scheduler and scheduler.get_jobs():
        scheduler.shutdown(wait=False)
    scheduler.add_job(clear_cache, 'interval',
                      minutes=CLEAN_CACHE_INTERVAL_MINUTES,
                      misfire_grace_time=600)
    scheduler.start()


if __name__ == '__main__':
    if os.path.exists(rec_tmp_dir):
        # 如果存在则删除文件，清理这些文件
        shutil.rmtree(rec_tmp_dir)
        # 创建缓存文件夹
        os.makedirs(rec_tmp_dir)
    else:
        # 创建缓存文件夹
        os.makedirs(rec_tmp_dir)

    # itchat.logout()  # 如果微信在线，则退出。重新登录。
    itchat.auto_login(loginCallback=before_login, exitCallback=after_logout)
    itchat.run(blockThread=True)
