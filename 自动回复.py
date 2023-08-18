import telebot
import logging

API_TOKEN = ''
admin_id =
bot = telebot.TeleBot(API_TOKEN)


keyword_responses = {}


logging.basicConfig(filename='bot.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')



@bot.message_handler(commands=['set_reply'])
def set_reply(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    user = bot.get_chat_member(chat_id, user_id)

    if user_id == admin_id:
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
        logging.info(f"管理员 {admin_name} 设置了关键字回复: '{keyword}': '{response}'")
    else:
        bot.reply_to(message, "只有管理员可以设置回复内容！")



@bot.message_handler(func=lambda message: any(keyword in message.text.lower() for keyword in keyword_responses.keys()))
def keyword_reply(message):
    for keyword, response in keyword_responses.items():
        if keyword in message.text.lower():
            bot.reply_to(message, response)
            logging.info(f"关键字'{keyword}'的回复被触发: '{message.text}'")
            break



def save_responses_to_file():
    with open('keyword_responses.txt', 'w') as file:
        for keyword, response in keyword_responses.items():
            file.write(f"{keyword}:{response}\n")


def load_responses_from_file():
    try:
        with open('keyword_responses.txt', 'r') as file:
            for line in file:
                keyword, response = line.strip().split(':', 1)
                keyword_responses[keyword] = response
    except FileNotFoundError:
        pass



@bot.message_handler(commands=['help'])
def show_help(message):
    help_text = """
    使用方法:
    - /set_reply 关键字 回复内容: 设置关键字回复
    - /help: 显示帮助信息
    """
    bot.reply_to(message, help_text)


if __name__ == '__main__':
    load_responses_from_file()
    print('程序启动')
    bot.polling()
