# 白云群管初代 宗旨:能用就行
from pyrogram import Client, filters, enums
from pyrogram.enums import ChatMemberStatus, ChatType, ChatMembersFilter
from pyrogram.errors import FloodWait
from pyrogram.types import Message, User, ChatPermissions, ChatMember, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup, MessageEntity
import time
import asyncio
from datetime import datetime, timedelta, timezone
import aiohttp
import json
import random
import yaml
import sqlite3
import datetime
import logging
import sys
import os
import re


async def aiohttpGet(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                return await resp.read()
            return None
def create_auto_reply_table():
    try:
        conn = sqlite3.connect("db/auto_reply.db")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS auto_reply (chatid INTEGER, keyword TEXT, response TEXT, PRIMARY KEY (chatid, keyword))")
        conn.commit()
        conn.close()
    except Exception as error:
        logging.error(error)
def InitBot():
    try:
        """
        初始化Bot关于一些参数以及配置 [待开发]
        """
        create_auto_reply_table()
        return True
    except Exception as error:
        logging.error(error)
async def CheckBot(Client):
    try:
        me = await Client.get_me()
        if me is None:
            return None
        return me
    except Exception as error:
        logging.error(error)
        return None
def keyword_exists(chatid, keyword):
    try:
        with sqlite3.connect("db/auto_reply.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM auto_reply WHERE chatid=? AND keyword=?", (chatid, keyword))
            count = cursor.fetchone()[0]
            return count > 0
    except sqlite3.Error as db_error:
        logging.error(f"SQLite error: {db_error}")
        return False
def delete_auto_reply(chatid, keyword):
    try:
        if not keyword_exists(chatid, keyword):
            return
        with sqlite3.connect("db/auto_reply.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM auto_reply WHERE chatid=? AND keyword=?", (chatid, keyword))
            conn.commit()
    except sqlite3.Error as db_error:
        logging.error(f"SQLite error: {db_error}")
async def CheckBotPermissions(Client, chatid, meid):
    try:
        result = await Client.get_chat_member(chatid, meid)
        if result.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return False
        else:
            return True
    except Exception as error:
        logging.error(error)
def check_missing_folders(required_folders):
    try:
        """
        检查当前工作目录是否缺少指定的文件夹。
        返回缺少的文件夹列表。
        """
        current_directory = os.getcwd()
        existing_folders = [item for item in os.listdir(current_directory) if os.path.isdir(item)]
        missing_folders = [folder for folder in required_folders if folder not in existing_folders]
        return missing_folders
    except Exception as error:
        logging.error(error)
def create_folders(folders_to_create):
    try:
        """
        在当前工作目录中创建指定的文件夹。
        """
        current_directory = os.getcwd()
        for folder in folders_to_create:
            folder_path = os.path.join(current_directory, folder)
            os.makedirs(folder_path, exist_ok=True)
            logging.info(f"创建了{folder}文件夹")
    except Exception as error:
        logging.error(error)
def loadConfigs():
    try:
        global configs
        global AutoReply
        required_folders = ["temp", "config", "logs", "plugins"]
        missing_folders = check_missing_folders(required_folders)
        if missing_folders:
            for folder in missing_folders:
                create_folders([folder])
        with open('config/config.yaml', mode='rt', encoding='utf-8') as file:
            configs = yaml.safe_load(file)
            return True
    except Exception as error:
        logging.error(error)
        return False
async def search_auto_reply(chatid, keyword):
    try:
        with sqlite3.connect("db/auto_reply.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT keyword, response FROM auto_reply WHERE chatid=? AND keyword LIKE ?", (chatid, f"%{keyword}%"))
            rows = cursor.fetchall()
            return rows  
    except sqlite3.Error as db_error:
        logging.error(f"SQLite error: {db_error}")
        return []
async def check_auto_reply(user_text, chat_id):
    try:
        auto_reply_results = read_auto_reply(chat_id)
        if auto_reply_results:
            for keyword in auto_reply_results:
                if keyword in user_text:
                    return auto_reply_results[keyword]
        else:
            return None
    except Exception as error:
        logging.error(error)
def write_auto_reply(chatid, keyword, response):
    try:
        with sqlite3.connect("db/auto_reply.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO auto_reply (chatid, keyword, response) VALUES (?, ?, ?)", (chatid, keyword, response))
            conn.commit()
    except sqlite3.Error as db_error:
        logging.error(f"SQLite error: {db_error}")

def read_auto_reply(chatid):
    try:
        with sqlite3.connect("db/auto_reply.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT keyword, response FROM auto_reply WHERE chatid=?", (chatid,))
            rows = cursor.fetchall()
        return {row[0]: row[1] for row in rows}
    except sqlite3.Error as db_error:
        logging.error(f"SQLite error: {db_error}")
        return {}
loadConfigs()
user_choices = {}
plugins = dict(root=configs.get('bot').get('plugins'))
app = Client(
    "my_bot",
    api_id=configs.get("bot").get("api_id", ""),
    api_hash=configs.get("bot").get("api_hash", ""),
    bot_token=configs.get("bot").get("token", ""),
    plugins=plugins,
    proxy=configs.get('bot').get("proxy")
)

logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/bot.log"),
        logging.StreamHandler()
    ]
)
def GetNowTime():
    try:
        utc_now = datetime.utcnow()
        utc_plus_8 = timezone(timedelta(hours=8))
        utc_plus_8_now = utc_now.replace(tzinfo=timezone.utc).astimezone(utc_plus_8)
        formatted_time = utc_plus_8_now.strftime("%Y-%m-%d %H:%M:%S")
        return formatted_time
    except Exception as error:
        logging.error(f"时间获取错误: {error}")
def check_banned_keywords(message_text):
    try:
        for keyword in configs.get('bot').get('banned_keywords'):
            try:
                if keyword.startswith("^") and re.match(keyword, message_text):
                    return True
                elif keyword.lower() in message_text.strip().lower():
                    return True
            except re.error as regex_error:
                logging.error(f"正则表达式错误: {regex_error}")
        return False
    except Exception as error:
        logging.error(error)
@app.on_message(filters.command("game"))
async def game_command(client, message):
    try:
        if message.from_user is None:
            return
        if message.chat.id in configs.get("bot").get('bangame', []):
            await message.reply_text(f"应管理员要求 这里屏蔽了/game")
            return
        if message.from_user.username is not None:
            await message.reply_text(f"@{message.from_user.username} 发起了一个游戏")
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("1", callback_data="1"),
             InlineKeyboardButton("2", callback_data="2"),
             InlineKeyboardButton("3", callback_data="3")],
            [InlineKeyboardButton("4", callback_data="4"),
             InlineKeyboardButton("5", callback_data="5"),
             InlineKeyboardButton("6", callback_data="6")]
        ])
        await message.reply_text("请选择一个结果：", reply_markup=keyboard)
    except FloodWait as error:
        await asyncio.sleep(error.value)
    except Exception as error:
        logging.error(error)
@app.on_callback_query()
async def handle_callback(client, callback_query):
    try:
        if callback_query.message.from_user is None:return
        result = await client.send_dice(callback_query.message.chat.id,"🎲")
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("再试一次", callback_data="game")]])
        if str(result.dice.value) == str(callback_query.data):
            await client.send_message(callback_query.message.chat.id, f"`{callback_query.message.from_user.id}` 恭喜您答对了 结果是:`{result.dice.value}`",  reply_markup=keyboard)
            await client.delete_messages(callback_query.message.chat.id, callback_query.message.id)
            return
        if str(callback_query.data) == "game":
            return
        await client.send_message(callback_query.message.chat.id, f"`{callback_query.from_user.id}` 没猜对 结果是: `{result.dice.value}` 您的选择为:`{callback_query.data}`", reply_markup=keyboard)
        await client.delete_messages(callback_query.message.chat.id, callback_query.message.id)
        return
    except FloodWait as error:
        await asyncio.sleep(error.value)
    except Exception as error:
        logging.error(error)
@app.on_message(filters.new_chat_members)
async def welcome_message(client, message):
    try:
        me = await client.get_me()
        if message.from_user is None:
            return
        chat_title = message.chat.title if message.chat.title else "这里"
        if message.new_chat_members and message.new_chat_members[0].id == me.id:
            if message.from_user.id != me.id and message.from_user.id not in configs.get("bot").get("Admins"):
                reply_message = await message.reply_text(f"`{message.from_user.id}` 请不要把我随意拉到群内，请联系Bot管理员")
                await client.leave_chat(message.chat.id)
                await asyncio.sleep(5)
                await client.delete_messages(message.chat.id, reply_message.message_id)
                return
            welcome_text = f"`{me.first_name}`在`{chat_title}`为您服务"
            reply_message = await message.reply_text(welcome_text)
            await asyncio.sleep(5)
            await client.delete_messages(message.chat.id, reply_message.message_id)
            return
        if message.new_chat_members[0].is_bot:
            await asyncio.sleep(5)
            await client.delete_messages(message.chat.id,message.id)
            return
        for new_member in message.new_chat_members:
            user_id = new_member.id
            dc_info = f"来自`DC{new_member.dc_id}`的" if new_member.dc_id is not None else ""
            welcome_text = f"欢迎{dc_info}`{new_member.first_name}` 来到 `{chat_title}`"
            reply_message = await message.reply_text(welcome_text)
            chat_member = await client.get_chat_member(message.chat.id, me.id)
            if chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                user_info = await client.get_users(user_id)
                if check_banned_keywords(user_info.first_name) and user_info.first_name is not None:
                    await client.restrict_chat_member(message.chat.id, user_id, ChatPermissions())
                    error_message = await message.reply_text(f"`{user_id}`名称中包含违禁词汇。禁言处理\n如果这是错的请向管理员反应")
                    await asyncio.sleep(5)
                    await client.delete_messages(message.chat.id, error_message.id)
            await asyncio.sleep(5)
            await client.delete_messages(message.chat.id, reply_message.id)
            await client.delete_messages(message.chat.id, message.id)
    except Exception as error:
        logging.error(error)
@app.on_message(filters.new_chat_title)
async def on_chat_title_change(client, message):
    try:
        new_title = message.new_chat_title
        await client.send_message(message.chat.id, f"`{message.from_user.id}` 将群组标题已更改为：`{new_title}`")
    except Exception as error:
        logging.error(error)
@app.on_message(filters.command("start"))
async def start_command(client, message):
    try:
        if message.from_user is None:
            return
        if message.from_user and message.from_user.is_bot:
            return
        me = await CheckBot(client)
        welcome_message = f"`{message.from_user.id}` 欢迎使用 `{me.first_name}`"
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🇨🇳简体中文", url="https://t.me/setlanguage/zhcncc"),InlineKeyboardButton("🇭🇰繁体中文", url="https://t.me/setlanguage/zh-hant-beta")]
        ])
        await message.reply_text(welcome_message, reply_markup=keyboard)
    except Exception as error:
        logging.error(error)
@app.on_message(filters.command("atadmins"))
async def AtAdminsCommand(Client, message):
    try:
        print("触发")
        if message.from_user is None:return
        if message.from_user.is_bot:return
        if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await message.reply_text("这是群组指令")
            return
        Admins = []
        async for admin in Client.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
            if not admin.user.is_bot and not admin.user.is_deleted:
                Admins.append(admin.user.mention)
        if Admins is None:
            await message.reply_text("本群没有管理员")
            return
        reply_text = f"<a href='tg://user?id={message.from_user.id}'>@{message.from_user.id}</a>: 管理员聆听我的召唤 出现吧\n\n"
        for admin in Admins:
            reply_text += f"    {admin}\n"
        await message.reply_text(reply_text)
    except Exception as error:
        logging.error(f"错误: {error}")
@app.on_message(filters.command("help"))
async def help_command(client, message):
    try:
        help_text = (
                "用户命令:\n"
                "`/start` - Bot的第一个命令\n"
                "`/my` - 查看用户信息\n"
                "`/help` - 查看如何使用机器人\n"
                "`/atadmins` - 呼叫管理员\n"
            )
        if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)
            if chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                help_text += (
                    "\n管理员命令:\n"
                    "`/ban` - 禁言一个用户\n"
                    "`/unban` - 解封用户\n"
                    "`/sb` - 封禁用户\n"
                    "`/pin` - 置顶消息\n"
                    "`/lr` - 列出自动回复\n"
                    "`/ar` - 新增自动回复\n"
                    "`/dr` - 删除自动回复\n"
                    "`/sr` - 搜索自动回复\n"
                    "`/unpin` - 解除置顶\n"
                    "`/templink` - 创建一个一次性邀请链接\n"
                    "`/change` - 更改群聊相关信息\n"
                )
        if message.from_user.id in configs.get("bot").get("Admins"):
            help_text += (
                "\n超管命令:\n"
                "`/reload` - 重载机器人配置\n"
                "`/leave` - 机器人离开群组\n"
                "`/restart` - 重启机器人\n"
                "`/logs` - 查看机器人日志\n"
                "`/send` - 发送一条指定消息"
            )
        message_delete = await message.reply_text(help_text)
        await asyncio.sleep(10)
        await client.delete_messages(message_ids=message_delete.id,chat_id=message.chat.id)
    except Exception as error:
        logging.error(f"发生错误: {error}")
@app.on_message(filters.command("my"))
async def my_command(client, message):
    try:
        is_group_message = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
        if message.from_user and message.from_user.is_bot:
            await message.reply_text('小小Bot 以下犯上定将你斩于马下')
            return
        if message.from_user is None:
            await message.reply_text("禁止频道或匿名管理员使用此命令")
            return
        me = await CheckBot(client)
        if is_group_message:
            if not await CheckBotPermissions(chatid=message.chat.id, Client=client, meid=me.id):
                await message.reply_text("我只是一个普通Bot 我手无缚鸡之力")
                return
        user_is_premium = 'Premium会员' if message.from_user.is_premium else '普通账户'
        chat_member, user_chat_member, joined_date = None, '未知', None
        if is_group_message:
            chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)
            user_chat_member = '普通用户' if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER] else '创始人' if chat_member.status == ChatMemberStatus.OWNER else '管理员'
            joined_date = chat_member.joined_date if chat_member.joined_date else "未知"
        reply_text = f"`{message.from_user.id}` 您的信息如下:\n"
        reply_text += f"   Telegram账户: `{user_is_premium}`\n"
        reply_text += f"   账户所处服务器: `{message.from_user.dc_id}`\n" if message.from_user.dc_id else ""
        reply_text += f"   当前语言: `{message.from_user.language_code}`\n" if message.from_user.language_code else ""
        reply_text += f"   ChatID: `{message.chat.id}`\n"
        if is_group_message:
            reply_text += f'   账户所处群聊权限: `{user_chat_member}`\n'
            if chat_member.custom_title is not None:
                reply_text += f'   账户所处群聊头衔: `{chat_member.custom_title}`\n' if chat_member and chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER] else ""
            reply_text += f'   加入时间: `{joined_date}`\n' if joined_date is not None else ""
        message_delete = await message.reply_text(reply_text)
        await asyncio.sleep(10)
        await client.delete_messages(message_ids=message_delete.id,chat_id=message.chat.id)
    except Exception as error:
        logging.error(f"发生错误: {error}")
        await message.reply_text("处理您的请求时发生错误，请稍后再试。")
@app.on_message(filters.command("ar"))
async def add_auto_reply(client, message):
    try:
        is_group_message = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
        if not is_group_message:
            await message.reply_text("⚠️ 这是群组指令")
            return
        if message.from_user and message.from_user.is_bot:
            await message.reply_text('小小Bot 以下犯上定将你斩于马下')
            return
        if message.from_user is None:
            await message.reply_text("禁止频道或匿名管理员使用此命令")
            return
        command_parts = message.text.split(" ", 2)
        if len(command_parts) == 3:
            keyword = command_parts[1]
            response = command_parts[2]
            chat_id = message.chat.id
            sender_member = await client.get_chat_member(chat_id, message.from_user.id)
            if sender_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                write_auto_reply(chat_id, keyword, response)
                await message.reply_text(f"已添加自动回复: `{keyword}` -> `{response}`")
            else:
                await message.reply_text("只有群组管理员可以使用此命令。")
        else:
            await message.reply_text("指令格式不正确。请使用：/ar 关键词 回复内容")
    except Exception as error:
        logging.error(error)
@app.on_message(filters.command("lr"))
async def list_auto_reply(client, message):
    try:
        is_group_message = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
        if not is_group_message:
            await message.reply_text("⚠️ 这是群组指令")
            return
        if message.from_user and message.from_user.is_bot:
            await message.reply_text('小小Bot 以下犯上定将你斩于马下')
            return
        if message.from_user is None:
            await message.reply_text("禁止频道或匿名管理员使用此命令")
            return
        chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text("仅限群组管理员使用")
            return
        result = read_auto_reply(message.chat.id)
        if not result:
            await message.reply_text('没有任何自动回复')
            return
        result_dict = '内容如下[前15]:\n'
        for key, reply_text in list(result.items())[:15]:
            result_dict += f"   `{key}` -> `{reply_text}`\n"
        await message.reply_text(result_dict)
    except Exception as error:
        logging.error(error)
@app.on_message(filters.command("tcpping"))
async def tcpping(client, message):
    try:
        if message.from_user and message.from_user.is_bot:
            await message.reply_text('小小Bot 以下犯上定将你斩于马下')
            return
        if message.from_user is None:
            await message.reply_text("禁止频道或匿名管理员使用此命令")
            return
        if len(message.text.split()) != 2:
            await message.reply_text("格式错误")
            return
        result = await aiohttpGet(f"https://v2.api-m.com/api/tcping?address={message.text.split()[1]}&port=80")
        if result is None:
            await message.reply_text("Api请求失效")
            return
        result = json.loads(result)
        result_status = result.get('code')
        if result_status and result_status != 200:
            await message.reply_text(f"`{message.text.split()[1]}`请求失败")
            return
        if result_status and str(result_status) == '200':
            reply_text = 'Tcpping:\n'
            reply_text += f"地址: `{result.get('data').get('address')}`\n"
            reply_text += f"ping: `{result.get('data').get('ping')}`\n"
            reply_text += f"端口: `{result.get('data').get('port')}`\n"
            await message.reply_text(reply_text)
        else:
            await message.reply_text(f"错误码: {result_status}")
    except Exception as error:
        logging.error(error)
@app.on_message(filters.command("dr"))
async def delete_auto_reply_command(client, message):
    try:
        is_group_message = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
        if not is_group_message:
            await message.reply_text("⚠️ 这是群组指令")
            return
        if message.from_user and message.from_user.is_bot:
            await message.reply_text('小小Bot 以下犯上定将你斩于马下')
            return
        if message.from_user is None:
            await message.reply_text("禁止频道或匿名管理员使用此命令")
            return
        chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text("仅限群组管理员使用")
            return
        command_args = message.text.split(maxsplit=1)
        if len(command_args) < 2:
            await message.reply_text("请提供要删除的关键词")
            return
        keyword_to_delete = command_args[1].strip()
        if keyword_exists(message.chat.id, keyword_to_delete):
            delete_auto_reply(message.chat.id, keyword_to_delete)
            await message.reply_text(f"已删除关键词 '`{keyword_to_delete}`' 的自动回复")
        else:
            await message.reply_text(f"关键词 '`{keyword_to_delete}`' 不存在，无法执行删除操作。")
    except Exception as error:
        logging.error(error)
@app.on_message(filters.command("sr"))
async def search_auto_reply_command(client, message: Message):
    try:
        is_group_message = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
        if not is_group_message:
            await message.reply_text("⚠️ 这是群组指令")
            return
        if message.from_user and message.from_user.is_bot:
            await message.reply_text('小小Bot 以下犯上定将你斩于马下')
            return
        if message.from_user is None:
            await message.reply_text("禁止频道或匿名管理员使用此命令")
            return
        chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text("仅限群组管理员使用")
            return
        command_args = message.text.split(maxsplit=1)
        if len(command_args) < 2:
            await message.reply_text("请提供要搜索的关键词")
            return
        keyword_to_search = command_args[1].strip()
        search_results = search_auto_reply(message.chat.id, keyword_to_search)
        if search_results:
            result_text = "搜索结果：\n"
            for keyword, response in search_results:
                result_text += f"`{keyword}` -> `{response}`\n"
            await message.reply_text(result_text)
        else:
            await message.reply_text(f"未找到包含关键词 '`{keyword_to_search}`' 的自动回复")
    except Exception as error:
        logging.error(error)
@app.on_message(filters.command("logs"))
async def send_logs(client: Client, message):
    try:
        if message.from_user is None:
            return
        if message.from_user.is_bot:
            return
        user_id = message.from_user.id
        if user_id not in configs.get('bot').get('Admins'):
            await message.reply_text(f"⚠️ 权限不足")
            return
        await app.send_document(message.chat.id,"logs/bot.log",caption="机器人日志")
    except Exception as error:
        logging.error(f"发生错误: {error}")
        await message.reply_text("发送日志时发生错误")
@app.on_message(filters.command("ban"))
async def ban_command(client: Client, message):
    try:
        if message.from_user and message.from_user.is_bot:
            await message.reply_text('小小Bot 以下犯上定将你斩于马下')
            return
        if message.from_user is None:
            await message.reply_text("禁止频道或匿名管理员使用此命令")
            return
        if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await message.reply_text("⚠️ 这是群组指令")
            return
        me = await CheckBot(client)
        if not await CheckBotPermissions(chatid=message.chat.id, Client=client, meid=me.id):
            await message.reply_text("我只是一个普通Bot 我手无缚鸡之力")
            return
        executer_info = await client.get_chat_member(message.chat.id, message.from_user.id)
        if executer_info.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text(f"⚠️ 权限不足")
            return
        user_id_to_ban = None
        if message.reply_to_message and message.reply_to_message.from_user:
            user_id_to_ban = message.reply_to_message.from_user.id
        elif len(message.command) > 1:
            user_id_arg = message.command[1]
            match = re.match(r"(\d+)", user_id_arg)
            user_id_to_ban = int(match.group(1)) if match else None
        if not user_id_to_ban:
            await message.reply_text("请回复要禁言的用户的消息或使用 /ban [用户id] 命令")
            return
        user_info = await client.get_chat_member(message.chat.id, user_id_to_ban)
        if user_info.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text("只能对普通用户生效")
            return
        await client.restrict_chat_member(message.chat.id, user_id_to_ban, ChatPermissions())
        await message.reply_text(f"`{user_id_to_ban}` 被 `{message.from_user.id}` 禁言 时间:永远")
    except Exception as error:
        logging.error(f"发生错误: {error}", exc_info=True)
        await message.reply_text("处理您的请求时发生错误，请稍后再试。")
@app.on_message(filters.command("sb"))
async def sb_command(client: Client, message):
    try:
        if message.from_user and message.from_user.is_bot:
            await message.reply_text('小小Bot 以下犯上定将你斩于马下')
            return
        if message.from_user is None:
            await message.reply_text("禁止频道或匿名管理员使用此命令")
            return
        if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await message.reply_text("⚠️ 这是群组指令")
            return
        me = await CheckBot(client)
        if not await CheckBotPermissions(chatid=message.chat.id, Client=client, meid=me.id):
            await message.reply_text("我只是一个普通Bot 我手无缚鸡之力")
            return
        executer_info = await client.get_chat_member(message.chat.id, message.from_user.id)
        if executer_info.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text("⚠️ 权限不足")
            return
        user_id_to_ban = None
        if message.reply_to_message and message.reply_to_message.from_user:
            user_id_to_ban = message.reply_to_message.from_user.id
        elif len(message.command) > 1:
            user_id_arg = message.command[1]
            match = re.match(r"(\d+)", user_id_arg)
            user_id_to_ban = int(match.group(1)) if match else None
        if not user_id_to_ban:
            await message.reply_text("请回复要封禁的用户的消息或使用 /ban [用户id] 命令")
            return
        user_info = await client.get_chat_member(message.chat.id, user_id_to_ban)
        if user_info.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text("只能对普通用户生效")
            return
        await client.ban_chat_member(message.chat.id, user_id_to_ban)
        await message.reply_text("`{user_id}` 被 `{executor_id}` 封禁 时间:永远".format(user_id=user_id_to_ban, executor_id=message.from_user.id))
    except Exception as error:
        logging.error(f"发生错误: {error}", exc_info=True)
        await message.reply_text("处理您的请求时发生错误，请稍后再试。")
@app.on_message(filters.command("forward"))
async def forward_command(client: Client, message):
    try:
        if message.from_user and message.from_user.is_bot:
            await message.reply_text('小小Bot 以下犯上定将你斩于马下')
            return
        if message.from_user is None:
            await message.reply_text("禁止频道或匿名管理员使用此命令")
            return
        if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await message.reply_text("⚠️ 这是群组指令")
            return
        if message.reply_to_message:
            await app.forward_messages(message.chat.id, message.chat.id, message.reply_to_message.id)
            await client.delete_messages(message_ids=message.id, chat_id=message.chat.id)
        else:
            await message.reply_text(f"请回复您要转发的消息")
    except Exception as error:
        logging.error(error)
@app.on_message(filters.command("unban"))
async def unban_command(client: Client, message):
    try:
        if message.from_user and message.from_user.is_bot:
            await message.reply_text('小小Bot 以下犯上定将你斩于马下')
            return
        if message.from_user is None:
            await message.reply_text("禁止频道或匿名管理员使用此命令")
            return
        if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await message.reply_text("⚠️ 这是群组指令")
            return
        me = await CheckBot(client)
        if not await CheckBotPermissions(chatid=message.chat.id, Client=client, meid=me.id):
            await message.reply_text("我只是一个普通Bot 我手无缚鸡之力")
            return
        chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER] and message.from_user.id not in configs.get("bot").get('Admins', []):
            await message.reply_text(f"⚠️ 权限不足")
            return
        user_id_to_unban = None
        if message.reply_to_message and message.reply_to_message.from_user:
            user_id_to_unban = message.reply_to_message.from_user.id
        elif len(message.command) > 1:
            user_id_arg = message.command[1]
            match = re.match(r"(\d+)", user_id_arg)
            if match:
                user_id_to_unban = int(match.group(1))
        if not user_id_to_unban:
            await message.reply_text("请回复要解除禁言的用户的消息或使用 /unban [用户id] 命令")
            return
        user_info = await client.get_chat_member(message.chat.id, user_id_to_unban)
        if user_info.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text("只能对普通用户生效")
            return
        await client.unban_chat_member(message.chat.id, user_id_to_unban)
        await message.reply_text(f"`{user_id_to_unban}` 已解除禁言")
    except Exception as error:
        logging.error(f"发生错误: {error}", exc_info=True)
        await message.reply_text("处理您的请求时发生错误，请稍后再试。")
        logging.error(error)
@app.on_message(filters.command("send"))
async def send_command(client, message):
    try:
        if message.from_user is None or message.from_user.id not in configs.get('bot').get('Admins', []):
            return
        if len(message.text.split()) != 3:
            await message.reply_text('格式错误')
            return
        result = await client.send_message(message.text.split()[1], message.text.split()[2])
        if result is not None:
            await message.reply_text(f"发送成功")
        else:
            await message.reply_text('发送失败')
    except Exception as error:
        logging.error(error)
@app.on_message(filters.command("templink"))
async def templink_command(client: Client, message):
    try:
        if message.from_user and message.from_user.is_bot:
            await message.reply_text('小小Bot 以下犯上定将你斩于马下')
            return
        if message.from_user is None:
            await message.reply_text("禁止频道或匿名管理员使用此命令")
            return
        if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await message.reply_text("⚠️ 这是群组指令")
            return
        me = await CheckBot(client)
        if not await CheckBotPermissions(chatid=message.chat.id, Client=client, meid=me.id):
            await message.reply_text("我只是一个普通Bot 我手无缚鸡之力")
            return
        executer_info = await client.get_chat_member(message.chat.id, message.from_user.id)
        if executer_info.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            await message.reply_text(f"⚠️ 权限不足")
            return
        link = await client.create_chat_invite_link(chat_id=message.chat.id,member_limit=1)
        if link is None:
            await message.reply_text(f"创建失败")
            return
        await message.reply_text(f"创建了一个一次性临时邀请链接:\n 创建时间: `{link.date}`\n 链接: `{link.invite_link}`")
    except Exception as error:
        logging.error(f"发生错误: {error}", exc_info=True)
        await message.reply_text("处理您的请求时发生错误，请稍后再试。")
@app.on_message(filters.command("pin"))
async def pin_command(client, message):
    try:
        if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await message.reply_text("⚠️ 这是群组指令")
            return
        me = await CheckBot(client)
        if not await CheckBotPermissions(chatid=message.chat.id, Client=client, meid=me.id):
            await message.reply_text("我只是一个普通Bot 我手无缚鸡之力")
            return
        chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER] and message.from_user.id not in configs.get("bot").get('Admins', []):
            await message.reply_text(f"⚠️ {message.from_user.id} 权限不足")
            return
        if message.reply_to_message:
            try:
                await client.pin_chat_message(chat_id=message.chat.id, message_id=message.reply_to_message.id)
                await message.reply_text("消息已置顶")
            except Exception as pin_error:
                await message.reply_text(f"消息置顶失败")
                logging.error(pin_error)
        else:
            await message.reply_text("请回复要置顶的消息或使用 /pin 命令")
    except Exception as error:
        logging.error(error)
@app.on_message(filters.command("unpin"))
async def unpin_command(client, message):
    try:
        if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await message.reply_text("⚠️ 这是群组指令")
            return
        me = await CheckBot(client)
        if not await CheckBotPermissions(chatid=message.chat.id, Client=client, meid=me.id):
            await message.reply_text("我只是一个普通Bot 我手无缚鸡之力")
            return
        chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member and chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER] or message.from_user.id in configs.get("bot").get('Admins', []):
            if not message.reply_to_message:
                await message.reply_text(f"请使用 /unpin 回复置顶的消息")
                return
            await client.unpin_chat_message(chat_id=message.chat.id, message_id=message.reply_to_message.id)
            await message.reply_text("消息已解除置顶")
        else:
            await message.reply_text(f"⚠️ {message.from_user.id} 权限不足，您不是管理员。")
    except Exception as error:
        logging.error(error)
        await message.reply_text(f"无法解除置顶消息")
@app.on_message(filters.command("change"))
async def change_command(client, message):
    try:
        if message.chat.type not in [ChatType.SUPERGROUP]:
            await message.reply_text("⚠️ 这个指令仅适用于超级群组")
            return
        me = await CheckBot(client)
        if me and not await CheckBotPermissions(chatid=message.chat.id, Client=client, meid=me.id):
            await message.reply_text("我只是一个普通Bot 我手无缚鸡之力")
            return
        chat_member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member and chat_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER] or message.from_user.id in configs.get("bot").get('Admins', []):
            if len(message.text.split()) < 3:
                await message.reply_text(f"格式错误")
                return
            if message.text.split()[1] not in ['describe', 'title']:
                await message.reply_text(f"更改的内容错误应该为: [`describe`] 或者 [`title`]")
                return
            if len(' '.join(message.text.split()[2:])) > 255:
                await message.reply_text(f"超出长度限制")
                return
            if message.text.split()[1] == "title":
                result = await client.set_chat_title(message.chat.id, ' '.join(message.text.split()[2:]))
                if not result:
                    await message.reply_text(f"更改失败")
                    return
                await message.reply_text(f"群聊标题更正为: `{' '.join(message.text.split()[2:])}`")
            if message.text.split()[1] == "describe":
                result = await client.set_chat_description(message.chat.id, ' '.join(message.text.split()[2:]))
                if not result:
                    await message.reply_text(f"更改失败")
                    return
                await message.reply_text(f"群聊描述更正为: `{' '.join(message.text.split()[2:])}`")
        else:
            await message.reply_text(f"⚠️ {message.from_user.id} 权限不足，您不是管理员。")
    except Exception as error:
        logging.error(error)
        await message.reply_text(f"更改失败")
@app.on_message(filters.command("reload"))
async def reload_command(client, message):
    try:
        if message.from_user is None:
            return
        if message.from_user and message.from_user.is_bot:
            return
        if message.from_user.id not in configs.get("bot").get('Admins', []):
            await message.reply_text(f"⚠️ {message.from_user.id} 权限不足")
            return
        result = loadConfigs()
        if not result:
            await message.reply_text(f"配置重载失败")
            return
        await message.reply_text(f"机器人配置已重载")
        logging.info(f"{message.from_user.id} 在 {message.chat.id} 使用/reload 重载了机器人配置")
    except Exception as error:
        logging.error(error)
@app.on_message(filters.command("leave"))
async def leave_command(client, message):
    try:
        if message.from_user is None:
            return
        if message.from_user and message.from_user.is_bot:
            return
        if message.from_user.id not in configs.get("bot").get('Admins', []):
            await message.reply_text(f"⚠️ {message.from_user.id} 权限不足")
            return
        await message.reply_text(f"{message.from_user.id} Bye~")
        await client.leave_chat(message.chat.id)
        logging.info(f"{message.from_user.id} 在 {message.chat.id} 使用/leave Bot离开了群聊")
    except Exception as error:
        logging.error(error)
@app.on_message(filters.command("restart"))
async def restart_command(client, message):
    try:
        if message.from_user is None:
            return
        if message.from_user and message.from_user.is_bot:
            return
        if message.from_user.id not in configs.get('Admins', []):
            await message.reply_text(f"⚠️ {message.from_user.id} 权限不足")
            return
        await message.reply_text(f"Bot正在重启")
        logging.info(f"{message.from_user.id} 在 {message.chat.id} 使用/restart Bot重启")
        python = sys.executable
        os.execl(python, python, *sys.argv)
    except Exception as error:
        logging.error(error)
@app.on_message(filters.group & ~filters.private)
async def bot_main(client, message):
    try:
        me = await CheckBot(client)
        if me is None:
            return
        if message.from_user and message.from_user.is_bot:
            return
        if not await CheckBotPermissions(chatid=message.chat.id, Client=client, meid=me.id):
            return
        if message.from_user is not None:
            result = await client.get_chat_member(message.chat.id, message.from_user.id)
            if result is None:
                return
            if result.status and result.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                return
        if message.text:
            if check_banned_keywords(message.text):
                if message.from_user and message.from_user.id in configs.get("bot").get('Admins', []):
                    return
                await client.delete_messages(chat_id=message.chat.id, message_ids=message.id)
        if message.text:
            result = await check_auto_reply(chat_id=message.chat.id, user_text=message.text)
            if result is not None:
                await message.reply_text(result)
    except Exception as error:
        logging.error(error)
def BotStart():
    try:
        logging.info(f"Bot开始初始化")
        result = InitBot()
        if not result:
            logging.info(f"Bot初始化失败")
            return
        logging.info(f"Bot初始化成功")
        logging.info(f"Admins: {configs.get('bot').get('Admins', [])}")
        logging.info(f"机器人启动")
        app.run()
    except Exception as error:
        logging.error(f"机器人错误: {error}")
if __name__ == "__main__":
    try:
        BotStart()
    except Exception as error:
        logging.error(f"机器人错误: {error}")