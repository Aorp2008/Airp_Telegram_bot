import telebot
from datetime import datetime
import pytz
import string
import random

timezone = pytz.timezone('Asia/Shanghai')
now = datetime.now(timezone)
now_time = now.strftime("%Y-%m-%d %H:%M:%S")

admin_id = 
token = ''
bot = telebot.TeleBot(token)


def log(message, change, username):
    with open('db/log.db', mode='a', encoding='utf-8') as log_file:
        log_file.write(f'{now_time} ---- {message.chat.id} ({username}) ---- 使用了 {change}\n')
        log_file.write(f'Message: {message.text}\n')
        log_file.write(f'Command: {message.text.split()[0]}\n')
        log_file.write(f'User ID: {message.from_user.id}\n')
        log_file.write(f'Username: {username}\n')
        log_file.write(f'Chat ID: {message.chat.id}\n')
        log_file.write('----------------------------------------\n')


def init_bot():
    with open('db/log.db', mode='w', encoding='utf-8') as init_log:
        init_log.write(f'{now_time}----初始化完成\n')
    bot.set_my_commands(
        commands=[
            telebot.types.BotCommand("start", "开始菜单"),
            telebot.types.BotCommand("new", "创建口令"),
            telebot.types.BotCommand("open", "兑换口令"),
            telebot.types.BotCommand("help", '帮助菜单'),
        ],
    )
    print('[初始化完成]')
    print('程序已启动')


def process_content(message):
    bot_user_id = message.from_user.id
    content = message.text
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
    db_file_path = 'db/text.db'
    with open(db_file_path, mode='a', encoding='utf-8') as db_file:
        db_file.write(f'{bot_user_id}----{code}----{content}----0\n')
    bot.reply_to(message, f'创建成功，口令:{code},Bot: @Baiyun_text_bot')


def open_content(message):
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    bot_username = first_name + last_name if first_name and last_name else first_name or last_name or "Unknown"
    bot_user_id = message.from_user.id
    code = message.text
    db_file_path = 'db/text.db'
    found_records = []  # 存储匹配的口令记录
    with open(db_file_path, mode='r+', encoding='utf-8') as db_file:
        lines = db_file.readlines()
        db_file.seek(0)
        for line in lines:
            line_user_id, line_code, content, exchanged = line.strip().split("----")
            if line_code == code:
                if exchanged == '0':
                    found_records.append(f'{line_user_id}----{line_code}----{content}----1\n')
                    bot.reply_to(message, f'密文内容为：{content}')
                    bot.send_message(admin_id, f'口令 {content} 已经被用户id:{bot_user_id} 用户名{bot_username} 兑换')
                else:
                    bot.reply_to(message, '口令已兑换过')
            else:
                db_file.write(line)

        db_file.truncate()

        # 将匹配的记录写回文件
        for record in found_records:
            db_file.write(record)

    if not found_records:
        bot.reply_to(message, '口令无效或密文不存在')


@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id != admin_id:
        bot.reply_to(message, '你没有管理员权限')
        return
    command_args = message.text.split()
    subcommand = command_args[1] if len(command_args) > 1 else ''
    if subcommand == 'list':
        db_file_path = 'db/text.db'
        with open(db_file_path, mode='r', encoding='utf-8') as db_file:
            result = ''
            for line in db_file:
                line_user_id, line_code, content, exchanged = line.strip().split("----")
                if line_code:
                    result += f'口令：{line_code}\n内容：{content}\n状态：{"已兑换" if exchanged == "1" else "未兑换"}\n\n'
            if result:
                bot.send_message(message.chat.id, result)
            else:
                bot.send_message(message.chat.id, '没有口令记录')
    elif subcommand == 'rm':
        with open('db/text.db', mode='w', encoding='utf-8') as rm:
            rm.write('')
        bot.send_message(admin_id, '数据已清空')


@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot_user_id = message.from_user.id
    command = message.text.split()[0]
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    bot_username = first_name + last_name if first_name and last_name else first_name or last_name or "Unknown"
    log(message, command, bot_username)
    if command == '/start':
        if bot_user_id == admin_id:
            bot.send_message(message.chat.id, '欢迎管理员')
        else:
            bot.send_message(message.chat.id, f'欢迎{bot_username}来到白云密文机器人')


@bot.message_handler(commands=['new'])
def main(message):
    command = message.text.split()[0]
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    bot_username = first_name + last_name if first_name and last_name else first_name or last_name or "Unknown"
    log(message, command, bot_username)
    bot.reply_to(message, '请回复兑换码对应的内容：')
    bot.register_next_step_handler(message, process_content)


@bot.message_handler(commands=['open'])
def open_command(message):
    command = message.text.split()[0]
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    bot_username = first_name + last_name if first_name and last_name else first_name or last_name or "Unknown"
    log(message, command, bot_username)
    bot.reply_to(message, '请输入口令：')
    bot.register_next_step_handler(message, open_content)


def start_bot():
    init_bot()
    bot.polling()


start_bot()
