import telebot
import random
from datetime import datetime
import pytz
import logging

TOKEN = ''

bot = telebot.TeleBot(TOKEN)

admins = [] 
participants = [] 
specified_winners = [] 
losers = []  
winners = []  
admin_id = 
keyword = ""  
num_winners = 0  
num_participants = 0  
prize = ""  
is_lottery_started = False  

timezone = pytz.timezone('Asia/Shanghai')
now = datetime.now(timezone)
now_time = now.strftime("%Y-%m-%d %H:%M:%S")

logging.basicConfig(filename='bot.log', level=logging.ERROR)


def init_bot():
    with open('log.db', mode='w', encoding='utf-8') as init_file:
        init_file.write(f'{now_time}----初始化完成\n')
    bot.set_my_commands(
        commands=[
            telebot.types.BotCommand("start", "开始菜单"),
            telebot.types.BotCommand("join", "加入"),
            telebot.types.BotCommand("help", '帮助菜单'),
        ],
    )
    print('[初始化完成]')
    print('程序已启动')


def get_now_time():
    current_time = datetime.now(timezone)
    return current_time.strftime("%Y-%m-%d %H:%M:%S")



def get_username(user):
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    return first_name + last_name


def log(message, change, username):
    with open('log.db', mode='a', encoding='utf-8') as log_file:
        log_file.write(f'{now_time} ---- {message.chat.id} ({username}) ---- 使用了 {change}')
        log_file.write(f'\nMessage: {message.text}\n')
        log_file.write(f'Command: {message.text.split()[0]}\n')
        log_file.write(f'User ID: {message.from_user.id}\n')
        log_file.write(f'Username: {username}\n')
        log_file.write(f'Chat ID: {message.chat.id}\n')
        log_file.write('----------------------------------------\n')


def log_lottery_result(result):
    with open('lottery.db', mode='a', encoding='utf-8') as log_file:
        log_file.write(f'{now_time} ---- 抽奖结果 ----\n')
        log_file.write(result)
        log_file.write('\n----------------------------------------\n')


@bot.message_handler(commands=['count'])
def count_participants(message):
    if message.from_user.id not in admins:
        bot.reply_to(message, "抱歉，你没有权限执行此操作")
        return

    count = len(participants)
    bot.reply_to(message, f"当前已经加入的人数：{count}")


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    bot_username = first_name + last_name if first_name and last_name else first_name or last_name or "Unknown"
    command = message.text.split()[0]
    log(message, command, bot_username)
    if message.from_user.id == admin_id:
        bot.reply_to(message,
                     "欢迎管理员\n使用命令 /new 创建新抽奖\n使用命令 /join 加入抽奖\n使用命令 /draw 开奖\n使用命令 /count 查看实时人数\n使用命令 /setwinner "
                     "指定中奖者\n 使用命令 /setloser 指定不中奖者 ")
    else:
        bot.reply_to(message,
                     "欢迎使用抽奖机器人！\n使用命令 /join 加入抽奖")


@bot.message_handler(commands=['new'])
def new_lottery(message):
    global is_lottery_started
    is_lottery_started = True

    username = get_username(message.from_user)
    command = message.text.split()[0]
    log(message, command, username)
    if message.from_user.id not in admins:
        bot.reply_to(message, "抱歉，你没有权限执行此操作")
        return

    args = message.text.split()[1:]
    if len(args) != 4:
        bot.reply_to(message, "请提供正确的参数：/new 关键字 中奖人数 总人数 奖品")
        return

    global keyword, num_winners, num_participants, prize
    keyword, num_winners, num_participants, prize = args[0], int(args[1]), int(args[2]), args[3]
    participants.clear()
    winners.clear()
    bot.reply_to(message,
                 f"新抽奖已创建！关键字：{keyword}，中奖人数：{num_winners}，总人数：{num_participants},Bot:@Baiyun_lottery_bot")
    bot.send_message(message.chat.id, f"奖品：{prize}")


@bot.message_handler(commands=['join'])
def join_lottery(message):
    if not is_lottery_started:
        bot.send_message(message.chat.id, "没有进行中的抽奖")
        return

    username = get_username(message.from_user)
    command = message.text.split()[0]
    log(message, command, username)
    args = message.text.split()[1:]
    if len(args) != 1:
        bot.send_message(message.chat.id, "请提供正确的参数：/join 关键字")
        return

    join_keyword = args[0]
    if join_keyword != keyword:
        bot.send_message(message.chat.id, "抽奖不存在")
        return

    if len(participants) == num_participants:
        bot.send_message(message.chat.id, "抽奖已满员，无法加入")
        bot.send_message(admin_id, '人员已经满了可以可以开奖了')

    if 0 < num_participants <= len(participants):
        bot.send_message(message.chat.id, "抽奖已满员，无法加入")
        return

    participants.append(message.from_user)
    bot.send_message(message.chat.id, f"你已成功加入抽奖！关键字：{join_keyword}")


@bot.message_handler(commands=['setwinner'])
def set_winner(message):
    if message.from_user.id not in admins:
        bot.reply_to(message, "抱歉，你没有权限执行此操作")
        return

    args = message.text.split()[1:]
    if len(args) < 1:
        bot.reply_to(message, "请提供正确的参数：/setwinner 中奖者ID")
        return

    winner_ids = [int(id) for id in args]
    specified_winners.clear()
    for user in participants:
        if user.id in winner_ids:
            specified_winners.append(user)

    if len(specified_winners) > num_winners:
        bot.reply_to(message, "指定的中奖者数量不能超过总的中奖人数")
        return

    bot.reply_to(message, "中奖者已设置")


@bot.message_handler(commands=['setloser'])
def set_loser(message):
    if message.from_user.id not in admins:
        bot.reply_to(message, "抱歉，你没有权限执行此操作")
        return

    args = message.text.split()[1:]
    if len(args) < 1:
        bot.reply_to(message, "请提供正确的参数：/setloser 用户ID")
        return

    loser_ids = [int(id) for id in args]
    losers.clear()
    for user in participants:
        if user.id in loser_ids:
            losers.append(user)

    bot.reply_to(message, "指定用户已设置为永不中奖")


@bot.message_handler(commands=['draw'])
def draw_lottery(message):
    global is_lottery_started
    is_lottery_started = False

    username = get_username(message.from_user)
    command = message.text.split()[0]
    log(message, command, username)
    if message.from_user.id not in admins:
        bot.reply_to(message, "抱歉，你没有权限执行此操作")
        return

    if len(participants) == 0:
        bot.reply_to(message, "当前没有参与抽奖的用户")
        return

    args = message.text.split()[1:]
    if message.from_user.id == admin_id:
        if len(args) == 1 and args[0] == 'force':
            bot.reply_to(message, "管理员强制开奖！")
            if len(winners) == int(num_winners) and len(participants) == int(num_participants):
                bot.reply_to(message, "抽奖已经完成，请勿重复开奖")
                return
            winners.clear()
            while len(winners) < int(num_winners):
                winner = random.choice(participants)
                if winner not in winners:
                    winners.append(winner)
        else:
            if len(winners) == int(num_winners):
                bot.reply_to(message, "抽奖已经完成，请勿重复开奖")
                return

            winners.clear()

            # 首先将指定的中奖者添加到 winners 列表中
            for user in specified_winners:
                winners.append(user)

            # 然后从未被指定为中奖者或不中奖者的参与者中随机选择剩余的中奖者
            remaining_participants = [user for user in participants if
                                      user not in specified_winners and user not in losers]
            while len(winners) < int(num_winners):
                winner = random.choice(remaining_participants)
                if winner not in winners:
                    winners.append(winner)

    result = "抽奖结果：\n"
    for i, winner in enumerate(winners):
        result += f"中奖人{i + 1}：{winner.first_name} (@{winner.username})\n"
        bot.send_message(admin_id, f"管理员通知{i + 1}：{winner.first_name} (@{winner.username})\n")

    log_lottery_result(result)  # 记录抽奖结果到日志文件

    bot.reply_to(message, result)

    for participant in participants:
        if participant in winners:
            bot.send_message(participant.id, f"恭喜你中奖了！中奖用户ID：{participant.id}，名称：{participant.first_name}")
            bot.send_message(participant.id, f"奖品：{prize}")
        else:
            bot.send_message(participant.id, result)

    participants.clear()


def bot_start():
    init_bot()
    bot.polling()


bot_start()
