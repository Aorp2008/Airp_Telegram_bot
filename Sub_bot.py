import os
import re
import time
import requests
import telebot
from datetime import datetime

import sqlite3
import telebot
import pandas as pd
from time import sleep
from loguru import logger

# 日志功能 记录用户使用的指令和获取的订阅日志
logger.add('bot.log')

# 定义bot管理员的telegram userid
admin_id = ['1363896545',]

# 定义bot
bot = telebot.TeleBot('6319050379:AAEbGbjiG82CcGN4TLYTt8NwHiaar-unMPI')

# 定义数据库
conn = sqlite3.connect('My_sub.db', check_same_thread=False)
c = conn.cursor()

# 定义自我介绍内容
intro = '本bot为@C1oudF1are的私人订阅小仓库bot 不对外公开'

# 创建表
c.execute('''CREATE TABLE IF NOT EXISTS My_sub(URL text, comment text)''')


# 初始化
def botinit():
    bot.delete_my_commands(scope=None, language_code=None)

    bot.set_my_commands(
        commands=[
            telebot.types.BotCommand("help", "帮助菜单"),
            telebot.types.BotCommand("add", "添加订阅"),
            telebot.types.BotCommand("del", "删除订阅"),
            telebot.types.BotCommand("search", "查找订阅"),
            telebot.types.BotCommand("update", "更新订阅"),
            telebot.types.BotCommand("subinfo", "订阅信息")
        ],
    )
    print('[初始化完成]')


# 接收用户输入的指令
@bot.message_handler(commands=['add', 'del', 'search', 'update', 'help'])
def handle_command(message):
    if str(message.from_user.id) in admin_id:
        command = message.text.split()[0]
        logger.debug(f"用户{message.from_user.id}使用了{command}功能")
        if command == '/add':
            add_sub(message)
        elif command == '/del':
            delete_sub(message)
        elif command == '/search':
            search_sub(message)
        elif command == '/update':
            update_sub(message)
        elif command == '/help':
            help_sub(message)
    else:
        # bot.send_message(message.chat.id, "你没有权限操作，别瞎搞！")
        bot.reply_to(message, "[WRONG][你没有操作权限]")


# 自我介绍
@bot.message_handler(commands=['start'], func=lambda message: message.chat.type == "private")
def start(message):
    bot.send_message(message.chat.id, intro, parse_mode='Markdown')


# 添加数据
def add_sub(message):
    try:
        url_comment = message.text.split()[1:]
        url = url_comment[0]
        comment = url_comment[1]
        c.execute("SELECT * FROM My_sub WHERE URL=?", (url,))
        if c.fetchone():
            bot.reply_to(message, "[WRONG][订阅已存在]")
        else:
            c.execute("INSERT INTO My_sub VALUES(?,?)", (url, comment))
            conn.commit()
            bot.reply_to(message, "[✅][添加成功]")
    except:
        bot.send_message(message.chat.id, "[WRONG][输入格式有误 请检查后重新输入]")


# 删除数据
def delete_sub(message):
    try:
        row_num = message.text.split()[1]
        c.execute("DELETE FROM My_sub WHERE rowid=?", (row_num,))
        conn.commit()
        bot.reply_to(message, "[✅][删除成功]")
    except:
        bot.send_message(message.chat.id, "[WRONG][输入格式有误 请检查后重新输入]")


# 查找数据
def search_sub(message):
    try:
        search_str = message.text.split()[1]
        c.execute("SELECT rowid,URL,comment FROM My_sub WHERE URL LIKE ? OR comment LIKE ?",
                  ('%' + search_str + '%', '%' + search_str + '%'))
        result = c.fetchall()
        if result:
            keyboard = []
            for i in range(0, len(result), 2):
                row = result[i:i + 2]
                keyboard_row = []
                for item in row:
                    button = telebot.types.InlineKeyboardButton(item[2], callback_data=item[0])
                    keyboard_row.append(button)
                keyboard.append(keyboard_row)
            total = len(result)
            keyboard.append([telebot.types.InlineKeyboardButton('❎关闭', callback_data='close')])
            reply_markup = telebot.types.InlineKeyboardMarkup(keyboard)
            bot.reply_to(message, f'已查询到{str(total)}条订阅', reply_markup=reply_markup)
        else:
            bot.reply_to(message, '[WRONG][没有查找到结果]')
    except:
        bot.send_message(message.chat.id, "[WRONG][输入格式有误 请检查后重新输入]")


# 更新数据
def update_sub(message):
    try:
        row_num = message.text.split()[1]
        url_comment = message.text.split()[2:]
        url = url_comment[0]
        comment = url_comment[1]
        c.execute("UPDATE My_sub SET URL=?, comment=? WHERE rowid=?", (url, comment, row_num))
        conn.commit()
        bot.reply_to(message, "[✅][更新成功]")
    except:
        bot.send_message(message.chat.id, "[WRONG][输入格式有误 请检查后重新输入]")


# 接收xlsx表格
@bot.message_handler(content_types=['document'])
def handle_document(message):
    if str(message.from_user.id) in admin_id:
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        try:
            file = bot.download_file(file_info.file_path)
            with open('sub.xlsx', 'wb') as f:
                f.write(file)
            df = pd.read_excel('sub.xlsx')
            for i in range(len(df)):
                c.execute("SELECT * FROM My_sub WHERE URL=?", (df.iloc[i, 0],))
                if not c.fetchone():
                    c.execute("INSERT INTO My_sub VALUES(?,?)", (df.iloc[i, 0], df.iloc[i, 1]))
                    conn.commit()
            bot.reply_to(message, "[✅][导入成功]")
        except:
            bot.send_message(message.chat.id, "[WRONG][导入的文件格式错误 请检查文件后缀是否为xlsx后重新导入]")
    else:
        bot.reply_to(message, "[WARNING][你不是管理员 禁止操作]")


def convert_time_to_str(time):
    # 时间数字转化成字符串，不够10的前面补个0
    if (time < 10):
        time = '0' + str(time)
    else:
        time = str(time)
    return time


def sec_to_data(y):
    h = int(y // 3600 % 24)
    d = int(y // 86400)
    h = convert_time_to_str(h)
    d = convert_time_to_str(d)
    return d + "天" + h + '小时'


def StrOfSize(size):
    def strofsize(integer, remainder, level):
        if integer >= 1024:
            remainder = integer % 1024
            integer //= 1024
            level += 1
            return strofsize(integer, remainder, level)
        elif integer < 0:
            integer = 0
            return strofsize(integer, remainder, level)
        else:
            return integer, remainder, level

    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
    integer, remainder, level = strofsize(size, 0, 0)
    if level + 1 > len(units):
        level = -1
    return ('{}.{:>03d} {}'.format(integer, remainder, units[level]))


def subinfo(url):
    headers = {'User-Agent': 'ClashforWindows/0.18.1'}
    try:
        message_raw = url
        final_output = ''
        url_list = re.findall("https?://[-A-Za-z0-9+&@#/%?=~_|!:,.;]+[-A-Za-z0-9+&@#/%=~_|]", message_raw)
        for url in url_list:
            try:
                res = requests.get(url, headers=headers, timeout=5)
            except:
                final_output = final_output + '订阅链接：`' + url + '`\n连接错误' + '\n\n'
                continue
            if res.status_code == 200:
                try:
                    info = res.headers['subscription-userinfo']
                    info_num = re.findall(r'\d+', info)
                    time_now = int(time.time())
                    output_text_head = '订阅链接：`' + url + '`\n已用上行：`' + StrOfSize(
                        int(info_num[0])) + '`\n已用下行：`' + StrOfSize(int(info_num[1])) + '`\n剩余：`' + StrOfSize(
                        int(info_num[2]) - int(info_num[1]) - int(info_num[0])) + '`\n总共：`' + StrOfSize(
                        int(info_num[2]))
                    if len(info_num) == 4:
                        timeArray = time.localtime(int(info_num[3]) + 28800)
                        dateTime = time.strftime("%Y-%m-%d", timeArray)
                        if time_now <= int(info_num[3]):
                            lasttime = int(info_num[3]) - time_now
                            output_text = output_text_head + '`\n过期时间：`' + dateTime + '`\n剩余时间：`' + sec_to_data(
                                lasttime) + '`'
                        elif time_now > int(info_num[3]):
                            output_text = output_text_head + '`\n此订阅已于`' + dateTime + '`过期！'
                    else:
                        output_text = output_text_head + '`\n到期时间：`没有说明捏`'
                except:
                    output_text = '订阅链接：`' + url + '`\n无流量信息'
            else:
                output_text = '订阅链接：`' + url + '`\n无法访问\n'
            final_output = final_output + output_text + '\n\n'
        return (final_output)
    except:
        return ('参数错误')


@bot.message_handler(commands=['subinfo'])
def get_subinfo(message):
    info_text = subinfo(message.text)
    try:
        bot.reply_to(message, info_text, parse_mode='Markdown')
    except:
        return


# 按钮点击事件
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if str(call.from_user.id) in admin_id:
        if call.data == 'close':
            bot.delete_message(call.message.chat.id, call.message.message_id)
        else:
            try:
                row_num = call.data
                c.execute("SELECT rowid,URL,comment FROM My_sub WHERE rowid=?", (row_num,))
                result = c.fetchone()

                headers = {'User-Agent': 'ClashforWindows/0.18.1'}
                output_test = ''
                try:
                    res = requests.get(result[1], headers=headers, timeout=5)
                except:
                    output_text = '连接错误'
                if res.status_code == 200:
                    try:
                        info = res.headers['subscription-userinfo']
                        info_num = re.findall(r'\d+', info)
                        time_now = int(time.time())
                        output_text_head = '上行：`' + StrOfSize(int(info_num[0])) + '`\n下行：`' + StrOfSize(
                            int(info_num[1])) + '`\n剩余：`' + StrOfSize(
                            int(info_num[2]) - int(info_num[1]) - int(info_num[0])) + '`\n总共：`' + StrOfSize(
                            int(info_num[2])) + '`'
                        if len(info_num) == 4:
                            timeArray = time.localtime(int(info_num[3]) + 28800)
                            dateTime = time.strftime("%Y-%m-%d", timeArray)
                            if time_now <= int(info_num[3]):
                                lasttime = int(info_num[3]) - time_now
                                output_text = output_text_head + '\n过期时间：`' + dateTime + '`\n剩余时间：`' + sec_to_data(
                                    lasttime) + '`'
                            elif time_now > int(info_num[3]):
                                output_text = output_text_head + '\n此订阅已于 `' + dateTime + '`过期'
                        else:
                            output_text = output_text_head + '\n过期时间：`没有说明`'
                    except:
                        output_text = '`无流量信息`'
                else:
                    output_text = '`无法访问`'

                bot.send_message(call.message.chat.id,
                                 '编号 `{}`\n订阅 `{}`\n说明 `{}`\n\n{}'.format(result[0], result[1], result[2],
                                                                                output_text), parse_mode='Markdown')
                logger.debug(f"用户{call.from_user.id}从BOT获取了{result}")
            except:
                bot.send_message(call.message.chat.id, "[WARNING][该订阅已被管理员删除]")
    else:
        if call.from_user.username is not None:
            now_user = f" @{call.from_user.username} "
        else:
            now_user = f" tg://user?id={call.from_user.id} "
        bot.send_message(call.message.chat.id, now_user + "[FBI WARNING]")


# 使用帮助
def help_sub(message):
    doc = '''添加订阅 /add url 备注
删除订阅 /del 行数
查找订阅 /search 内容
更新订阅 /update 编号 订阅链接 备注
导入订阅 发送xlsx表格[A列为订阅地址 B列为对应的备注]
    '''
    bot.send_message(message.chat.id, doc)


if __name__ == '__main__':
    print('[程序已启动]')
    botinit()
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            sleep(30)