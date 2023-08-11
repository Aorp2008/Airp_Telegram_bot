import telebot
import random
import time
import os

bot = telebot.TeleBot("")
last_command_time = {}
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id

    if user_id in last_command_time:
        current_time = time.time()
        if current_time - last_command_time[user_id] < 300:
            bot.reply_to(message, "Airp提醒您:每个人每5分钟只能获取一次")
            return
    
    if not os.path.exists("nodes.txt"):
        with open("nodes.txt", "w") as file:
            file.write("请在此文件写入节点")
    
    with open("nodes.txt", "r") as file:
        nodes = file.readlines()
    
    random_node = random.choice(nodes).strip()
    message_user = "节点为:"
    mess = message_user + random_node
    bot.reply_to(message, mess)
    
    last_command_time[user_id] = time.time()

bot.polling()
