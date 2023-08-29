import telebot
from subinfo import subinfo

token = ''
bot = telebot.TeleBot(token)
admin = []

def Sub_File(name, url):
    with open('Sub.db', mode='a', encoding='utf-8') as file:
        file.write(f'{name}----{url}\n')


@bot.message_handler(commands=['help'])
def bot_help(message):
    if message.from_user.id not in admin:
        bot.reply_to(message, '权限不足')
        return
    bot.send_message(message.chat.id,
                     '这里是Airp的专属订阅管理机器人\n /sub 名称 链接 用于一个订阅\n /search 名称 用于检索保存的订阅\n /subinfo 链接 用于检索订阅的状态')


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, '这里是Airp的专属订阅管理机器人')


@bot.message_handler(commands=['sub'])
def sub_new(message):
    if message.from_user.id not in admin:
        bot.reply_to(message, '权限不足')
        return
    args = message.text.split()
    if len(message.text.split()) == 3:
        Sub_File(args[1], args[2])
        bot.reply_to(message, '保存成功')
    else:
        bot.reply_to(message, '参数不足')


@bot.message_handler(commands=['search'])
def search(message):
    if message.from_user.id not in admin:
        bot.reply_to(message, '权限不足')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, '格式错误')
        return
    with open('Sub.db', mode='r', encoding='utf-8') as open_file:
        for name in open_file:
            name, url = name.strip().split('----')
            if name == args[1]:
                bot.reply_to(message, f'找到了订阅\n 名称:  {name}\n 链接:  {url}')
                break
        else:
            bot.reply_to(message, '没找到相应的订阅')


@bot.message_handler(commands=['subinfo'])
def bot_subinfo(message):
    if message.from_user.id not in admin:
        bot.reply_to(message, '权限不足')
        return
    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, '参数不足')
    bot.send_message(message.chat.id, subinfo(args[1]))


print('开始运行')
bot.polling()
