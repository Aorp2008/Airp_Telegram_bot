import telebot
import random
import time
import yaml

with open('config.yaml', 'rt') as file:
    config = yaml.safe_load(file)
Admin_name = config.get('admin_name', '')
admins = config.get('admin', '')
bot = telebot.TeleBot(config.get('token', ''))
current_time = time.ctime()


def log(chenge, userid):
    with open("log.txt", mode='a', encoding='utf-8') as log_file:
        log_file.write(f"{current_time}----Userid:{userid}----使用了{chenge}\n")


def botinit():
    bot.delete_my_commands(scope=None, language_code=None)
    open('nodes.txt', mode='a')
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


if __name__ == '__main__':
    while True:
        print('机器人启动')
        try:
            botinit()
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"出现了错误: {e}")
