import telebot
import datetime
import random
from collections import defaultdict
import yaml
import logging
import sys

with open('config.yaml', 'rt') as file:
    config = yaml.safe_load(file)

keywords_to_delete = config.get('keywords_to_delete', [])
Token = config.get('token', '')
admins = config.get('admins', [])
BotStatus = True
bot = telebot.TeleBot(Token)

Banme_Server = True
keyword_responses = {}
message_limit = config.get('message_limit', 16)
ban_duration = config.get('ban_duration', 600)
user_command_count = defaultdict(int)
ban_duration_on_limit = config.get('ban_duration_on_limit', 300)
user_warnings = defaultdict(int)
warning_limit = config.get('warning_limit', 5)
ban_duration_for_warnings = config.get('ban_duration_for_warnings', 60)
auto_reply_enabled = True
user_message_timestamps = defaultdict(list)
user_report_counts = defaultdict(int)
user_last_report_date = defaultdict(datetime.date)
keywords_to_delete_quantity = config.get('keywords_to_delete_quantity', 30)
user_request_counts = defaultdict(int)
user_last_request_date = defaultdict(datetime.date)
user_key_delete = {}


logging.basicConfig(filename='bot_log.log', level=logging.INFO)
logger = logging.getLogger(__name__)

def is_admin(user_id):
    return user_id in admins


def get_user_status(message):
    user_status = bot.get_chat_member(message.chat.id, message.from_user.id).status
    return user_status


def get_user_status_in_chat(chat_id, user_id):
    user_status = bot.get_chat_member(chat_id, user_id).status
    return user_status


def load_responses_from_file():
    try:
        with open('keyword_responses.txt', 'r') as keyword_file:
            for line in keyword_file:
                keyword, response = line.strip().split(':', 1)
                keyword_responses[keyword] = response
    except FileNotFoundError:
        pass


def save_responses_to_file():
    with open('keyword_responses.txt', 'w') as keyword_file:
        for keyword, response in keyword_responses.items():
            keyword_file.write(f"{keyword}:{response}\n")


@bot.message_handler(content_types=['new_chat_members'])
def greet_new_members(message):
    full_name = f"{message.from_user.first_name} {message.from_user.last_name}" if message.from_user.last_name else message.from_user.first_name
    new_members = message.new_chat_members
    text = config.get('welcome_text', '')
    welcome_text = f'{message.from_user.id} {full_name},{text}'
    for new_member in new_members:
        if new_member.is_bot:
            continue
        bot.send_message(message.chat.id, welcome_text)


@bot.message_handler(content_types=['left_chat_member'])
def on_member_left(message):
    left_member = message.left_chat_member
    if left_member.is_bot:
        return
    chat_id = message.chat.id
    bot.send_message(chat_id, f"{left_member.first_name} 离开了群聊！我们会想念你的。")


@bot.message_handler(commands=['getchat'])
def bot_getchar(message):
    bot.reply_to(message, f'当前聊天id为: {message.chat.id}')


@bot.message_handler(commands=['send'])
def bot_send(message):
    try:
        args = message.text.split()
        if message.from_user.id not in admins:
            print('权限不足')
        if len(args) != 3:
            bot.reply_to(message, f'格式错误: {args}')
        bot.send_message(args[1], args[2])
        bot.reply_to(message, '消息发送完毕')
    except Exception as error:
        logger.error(f'出现了错误: {error}')


@bot.message_handler(commands=['stop'])
def bot_stop(message):
    if message.from_user.id not in admins:
        bot.delete_message(message.chat.id, message.message_id)
        return
    global BotStatus
    BotStatus = False
    bot.reply_to(message, '机器人正在关闭...')
    sys.exit()
@bot.message_handler(commands=['start'])
def bot_start(message):
    user_status = get_user_status(message)
    if message.from_user.id in admins:
        bot.reply_to(message, '林公公参见皇上')
        return
    if user_status in ['administrator', 'creator']:
        bot.reply_to(message, '林公公参见贵人')
        return
    bot.reply_to(message, '平身')

@bot.message_handler(commands=['set_reply'])
def set_reply(message):
    user = bot.get_chat_member(message.chat.id, message.from_user.id)
    if message.from_user.id in admins:
        admin_name = user.user.first_name + (" " + user.user.last_name if user.user.last_name else "")
        args = message.text.split(' ', 2)
        if len(args) < 3:
            bot.reply_to(message, "使用方法: /set_reply 关键字 回复内容")
            return
        keyword = args[1].lower()
        response = args[2]
        keyword_responses[keyword] = response
        save_responses_to_file()
        bot.reply_to(message, f"{admin_name} 已设置关键字'{keyword}'的回复为: {response}")


@bot.message_handler(commands=['disable_auto_reply'])
def disable_auto_reply(message):
    if message.from_user.id not in admins:
        return
    global auto_reply_enabled
    auto_reply_enabled = False
    bot.reply_to(message, '自动回复已关闭')


@bot.message_handler(commands=['banme'])
def banme(message):
    if not Banme_Server:
        return
    try:
        if message.from_user is None:
            return
        full_name = f"{message.from_user.first_name} {message.from_user.last_name}" if message.from_user.last_name else message.from_user.first_name
        user_id = message.from_user.id
        chat_id = message.chat.id
        user_status = get_user_status_in_chat(chat_id, user_id)
        if user_status not in ['administrator', 'creator']:
            if user_status == 'restricted':
                message.delete(message)
                return
            else:
                additional_time = int(random.uniform(1, 1800))
                new_restriction = datetime.datetime.now() + datetime.timedelta(seconds=additional_time)
            bot.restrict_chat_member(chat_id, user_id, until_date=new_restriction)
            bot.reply_to(message,
                         f"{full_name} 您获得 {additional_time} 秒禁言时间，总禁言时间至 {new_restriction}")
        else:
            bot.reply_to(message, '仅对普通用户生效')
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(f'出现了错误: {e}')


@bot.message_handler(commands=['warn'])
def warn_user(message):
    user_status = get_user_status(message)
    if user_status not in ['administrator', 'creator']:
        message.delete(message)
    if not message.reply_to_message:
        bot.reply_to(message, "请回复您想要警告的用户的消息。")
        return

    warned_user_id = message.reply_to_message.from_user.id
    current_warnings = user_warnings[warned_user_id] + 1
    user_warnings[warned_user_id] = current_warnings

    bot.send_message(message.chat.id, f"用户 {warned_user_id} 被警告。警告次数：{current_warnings}/{warning_limit}")

    if current_warnings >= warning_limit:
        bot.restrict_chat_member(message.chat.id, warned_user_id,
                                 until_date=datetime.datetime.now() + datetime.timedelta(
                                     seconds=ban_duration_for_warnings))
        bot.send_message(message.chat.id, f"用户 {warned_user_id} 因多次警告，已被禁言。")
        user_warnings[warned_user_id] = 0


@bot.message_handler(commands=['enable_auto_reply'])
def enable_auto_reply(message):
    if message.from_user.id not in admins:
        message.delete(message)
    global auto_reply_enabled
    auto_reply_enabled = True
    bot.reply_to(message, '自动回复已打开')


@bot.message_handler(commands=['list'])
def list_responses(message):
    if message.from_user.id not in admins:
        message.delete(message)
    if keyword_responses:
        response_list = '\n'.join([f"{keyword}: {response}" for keyword, response in keyword_responses.items()])
        bot.reply_to(message, f"当前的自动回复列表:\n{response_list}")
    else:
        bot.reply_to(message, "当前没有设置任何自动回复。")


@bot.message_handler(commands=['reload'])
def reload(message):
    if message.from_user.id not in admins:
        message.delete(message)
    try:
        load_responses_from_file()
        bot.send_message(message.chat.id, '[Bot]配置文件已重载')
    except Exception as e:
        logger.error(f'配置文件重载失败: {e}')


@bot.message_handler(commands=['ban'])
def ban_user(message):
    try:
        if message.from_user.id not in admins:
            bot.delete_message(message.chat.id, message.message_id)
            return

        args = message.text.split()

        if len(args) == 1:
            bot.reply_to(message, "格式错误，请使用 '/ban [用户ID] [分钟]' 的格式，或者回复要禁言的消息。")
            return

        if message.reply_to_message and message.reply_to_message.from_user:
            if len(args) != 3:
                bot.reply_to(message, "格式错误，请使用 '/ban [用户ID] [分钟]' 的格式，或者回复要禁言的消息。")
                return
            user_id = message.reply_to_message.from_user.id
            ban_duration = int(args[2])

        else:
            if len(args) != 3:
                bot.reply_to(message, "格式错误，请使用 '/ban [用户ID] [分钟]' 的格式，或者回复要禁言的消息。")
                return

            user_id = int(args[1])
            ban_duration = int(args[2])
        bot.restrict_chat_member(message.chat.id, user_id,
                                 until_date=datetime.datetime.now() + datetime.timedelta(minutes=ban_duration))
        bot.reply_to(message, f"用户 {user_id} 已被禁言 {ban_duration} 分钟。")

    except Exception as e:
        logger.error(f'出现了错误: {e}')




@bot.message_handler(commands=['kick'])
def kick(message):
    if message.from_user.id not in admins():
        message.delete(message)
        return

    user_status = get_user_status_in_chat(message.chat.id, message.from_user.id)
    if user_status not in ['administrator', 'creator']:
        message.delete(message)
        return

    target_user_id = message.reply_to_message.from_user.id
    target_user_status = get_user_status_in_chat(message.chat.id, target_user_id)

    if target_user_status in ['administrator', 'creator']:
        bot.reply_to(message, '权限不足，无法踢出权限>=群管的用户')
        return

    bot.kick_chat_member(message.chat.id, target_user_id)
    bot.reply_to(message, f'{target_user_id} 已被踢出')



@bot.message_handler(commands=['unban'])
def unban(message):
    if message.from_user.id not in admins:
        bot.delete_message(message.chat.id, message.message_id)
        return
    try:
        if message.reply_to_message:
            target_user_id = message.reply_to_message.from_user.id
            bot.unban_chat_member(message.chat.id, target_user_id)
            bot.reply_to(message, f"用户 {target_user_id} 已解除封禁")
    except telebot.apihelper.ApiTelegramException as e:
        logger.error(f'出现了错误: {e}')

@bot.message_handler(commands=['help'])
def help_command(message):
    user_status = get_user_status(message)

    if is_admin(message.from_user.id):
        help_text = """
        您是管理员，可以使用以下指令：
        - `/getchat`: 获取当前聊天 ID。
        - `/send [chat_id] [message]`: 向指定聊天发送消息。
        - `/stop`: 关闭机器人（只有管理员有权执行）。
        - `/set_reply [keyword] [response]`: 设置关键词自动回复。
        - `/disable_auto_reply`: 关闭自动回复。
        - `/banme`: 对普通用户进行短暂的禁言。
        - `/warn`: 给用户发送警告。
        - `/enable_auto_reply`: 开启自动回复。
        - `/list`: 列出当前的自动回复列表。
        - `/reload`: 重载配置文件。
        - `/ban [minutes]`: 禁言用户。
        - `/kick`: 踢出用户。
        - `/unban`: 解封禁用户。
        """
    else:
        help_text = """
        您是普通用户，可以使用以下指令：
        - `/getchat`: 获取当前聊天 ID。
        - `/banme`: M专属指令。
        """

    bot.reply_to(message, help_text)


@bot.message_handler(func=lambda message: auto_reply_enabled and any(
    keyword in message.text.lower() for keyword in keyword_responses.keys()))
def keyword_reply(message):
    for keyword, response in keyword_responses.items():
        if keyword in message.text.lower():
            bot.reply_to(message, response)

@bot.message_handler(func=lambda message: True)
def count_messages(message, user_key_delete=None):
    if is_admin(message.from_user.id):
        return

    timestamps = user_message_timestamps[message.from_user.id]
    one_minute_ago = datetime.datetime.now() - datetime.timedelta(minutes=1)
    timestamps = [timestamp for timestamp in timestamps if timestamp > one_minute_ago]
    timestamps.append(datetime.datetime.now())
    user_message_timestamps[message.from_user.id] = timestamps

    if len(timestamps) > message_limit:
        bot.restrict_chat_member(message.chat.id, message.from_user.id,
                                 until_date=datetime.datetime.now() + datetime.timedelta(seconds=ban_duration_on_limit))
        bot.send_message(message.chat.id, f"用户 {message.from_user.id} 发言过快，已被禁言5分钟.")
        user_message_timestamps[message.from_user.id] = []

    if any(keyword in message.text for keyword in keywords_to_delete):
        try:
            bot.delete_message(message.chat.id, message.message_id)
            if user_key_delete.get(message.from_user.id) is None:
                user_key_delete[message.from_user.id] = 1
            else:
                user_key_delete[message.from_user.id] += 1
                if user_key_delete[message.from_user.id] >= keywords_to_delete_quantity:
                    user_key_delete[message.from_user.id] = 0
                    bot.restrict_chat_member(message.chat.id, message.from_user.id,
                                             until_date=datetime.datetime.now() + datetime.timedelta(
                                                 seconds=ban_duration_on_limit * 5))
        except telebot.apihelper.ApiTelegramException as error:
            logger.error(f'删除消息时出现错误: {error}')

    if message.from_user.is_bot:
        try:
            bot.delete_message(message.chat.id, message.message_id)
        except telebot.apihelper.ApiTelegramException as error:
            logger.error(f'删除机器人消息时出现错误: {error}')
if __name__ == '__main__':
    while BotStatus:
        try:
            print('机器人启动')
            load_responses_from_file()
            bot.polling(none_stop=True)
        except Exception as error:
            logger.error(f'出现了错误: {error}')
    print('机器人已停止')
