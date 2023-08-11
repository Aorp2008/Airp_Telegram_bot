import telebot
import random
import time

Admin_name = ''  # 你的用户名
admin_id = ''  # 你的Telegram用户id
bot = telebot.TeleBot("66506415077:AAESgxwEJUt5xT1XDBiS4AV961aHuV8V_vA")
current_time = time.ctime()


def log(chenge, userid):
    with open("log.txt", mode='a', encoding='utf-8') as log_file:
        log_file.write(f"{current_time}----Userid:{userid}----使用了{chenge}\n")


def botinit():
    bot.delete_my_commands(scope=None, language_code=None)
    with open('nodes.txt',mode='w',encoding='utf-8')as init_file:
        pass
    bot.set_my_commands(
        commands=[
            telebot.types.BotCommand("start", "开始菜单"),
            telebot.types.BotCommand("free", "获取节点"),

        ],
    )
    print('[初始化完成]')


@bot.message_handler(commands=['start', 'free', 'info', 'help', 'log'])
def main(message):
    user_id = message.from_user.id
    command = message.text.split()[0]
    if command == '/start':
        log(command, user_id)
        bot.send_message(message.chat.id, f'Hello {user_id} ,这里是{Admin_name}的免费节点机器人')
    elif command == '/free':
        log(command, user_id)
        with open("nodes.txt", "r") as file:
            nodes = file.readlines()
        random_node = random.choice(nodes).strip()
        bot.reply_to(message, random_node)
    elif command == '/help':
        log(command, user_id)
        bot.send_message(message.chat.id, '使用 /free 免费获取一条节点')
    else:
        bot.send_message(message.chat.id, '错误的指令')


botinit()
print("程序已启动")
bot.polling()
