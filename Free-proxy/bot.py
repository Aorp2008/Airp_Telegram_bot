import telebot
import time
import random
from datetime import datetime, timezone, timedelta
import threading
import yaml
with open('config.yaml', 'rt') as file:
    config = yaml.safe_load(file)
bot = telebot.TeleBot(config.get('Token'))
def get_time():
    utc_offset = timedelta(hours=8)
    utc_8_timezone = timezone(utc_offset)
    current_utc_time = datetime.utcnow().replace(tzinfo=timezone.utc).astimezone(utc_8_timezone)
    return current_utc_time

def send_message_periodically():
    while True:
        try:
            with open('proxy.txt', mode='rt', encoding='utf-8') as file:
                lines = file.readlines()
                if lines:
                    random_message = random.choice(lines)
                    result = f"免费节点 每小时更新一次 更新时间: {get_time().strftime('%Y-%m-%d %H:%M:%S')}\n\n{random_message}"
                    bot.send_message(config.get('Link'), result)
        except FileNotFoundError:
            print("File 'proxy.txt' not found.")
            open('proxy.txt', mode='w', encoding='utf-8').write('在这里填充节点 每行一个')
        except Exception as e:
            print(f"An error occurred: {e}")
        time.sleep(3600)

@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "欢迎来到Abox的免费节点机器人")

@bot.message_handler(commands=['update'])
def update(message):
    try:
        if message.from_user.id not in config.get('admins'):
            bot.reply_to(message, '权限不足')
        with open('proxy.txt', mode='rt', encoding='utf-8') as file:
            lines = file.readlines()
            if lines:
                random_message = random.choice(lines)
                result = f"免费节点 来自 {message.from_user.id} 管理员的手动更新 更新时间: {get_time().strftime('%Y-%m-%d %H:%M:%S')}\n\n{random_message}"
                bot.send_message(config.get('Link'), result)
                bot.reply_to(message, f"{get_time().strftime('%Y-%m-%d %H:%M:%S')}\n 新的节点已推送")
    except FileNotFoundError:
        print("File 'proxy.txt' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def run_bot():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as error:
            print(error)
            time.sleep(5)  

if __name__ == "__main__":
    print('开始运行')
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    periodic_thread = threading.Thread(target=send_message_periodically)
    periodic_thread.start()

    bot_thread.join()
    periodic_thread.join()