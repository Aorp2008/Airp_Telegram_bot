import sqlite3
import telebot
import pytz
import string
import random
import logging

logging.basicConfig(filename='db/log.db', level=logging.INFO, format='%(asctime)s - %(message)s')

timezone = pytz.timezone('Asia/Shanghai')

admin_id = '' 
token = ''  
bot = telebot.TeleBot(token)

with sqlite3.connect('db/text.db') as con:
    cur = con.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS codes
                (user_id TEXT, code TEXT, content TEXT, exchanged INTEGER)''')


def get_username(user):
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    return first_name + last_name if first_name and last_name else first_name or last_name or "Unknown"


def log(message, username):
    logging.info(f'{message.chat.id} ({username}) ---- 使用了 {message.text.split()[0]}\n'
                 f'Message: {message.text}\n'
                 f'User ID: {message.from_user.id}\n'
                 f'Username: {username}\n'
                 f'Chat ID: {message.chat.id}\n'
                 '----------------------------------------\n')


def process_content(message):
    try:
        bot_user_id = message.from_user.id
        content = message.text
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        cur.execute("INSERT INTO codes VALUES (?, ?, ?, ?)", (bot_user_id, code, content, 0))
        con.commit()
        bot.reply_to(message, f'创建成功，口令:{code},Bot: @Baiyun_text_bot')
    except Exception as e:
        logging.error(f"处理内容时发生错误: {e}")
        bot.reply_to(message, "处理内容时发生错误，请稍后重试。")


def open_content(message):
    try:
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name
        bot_username = get_username(message.from_user)
        bot_user_id = message.from_user.id
        code = message.text
        cur.execute("SELECT * FROM codes WHERE code = ?", (code,))
        row = cur.fetchone()
        if row:
            if row[3] == 0:
                cur.execute("UPDATE codes SET exchanged = 1 WHERE code = ?", (code,))
                con.commit()
                bot.reply_to(message, f'密文内容为：{row[2]}')
                bot.send_message(admin_id, f'口令 {row[2]} 已经被用户id:{bot_user_id} 用户名{bot_username} 兑换')
            else:
                bot.reply_to(message, '口令已兑换过')
        else:
            bot.reply_to(message, '口令无效或密文不存在')
    except Exception as e:
        logging.error(f"打开内容时发生错误: {e}")
        bot.reply_to(message, "打开内容时发生错误，请稍后重试。")


@bot.message_handler(commands=['start', 'help'])
def start(message):
    bot_user_id = message.from_user.id
    bot_username = get_username(message.from_user)
    log(message, bot_username)
    if bot_user_id == admin_id:
        bot.send_message(message.chat.id, '欢迎管理员')
    else:
        bot.send_message(message.chat.id, f'欢迎{bot_username}来到白云密文机器人')


@bot.message_handler(commands=['new'])
def new_command(message):
    bot.reply_to(message, '请回复兑换码对应的内容：')
    bot.register_next_step_handler(message, process_content)


@bot.message_handler(commands=['open'])
def open_command(message):
    bot.reply_to(message, '请输入口令：')
    bot.register_next_step_handler(message, open_content)


while True:
    print('机器人启动')
    try:
        bot.polling()
    except Exception as e:
        print(f"出现了错误: {e}")
