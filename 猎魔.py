# Airp开发出现任何问题概不负责
from pyrogram import Client
from pagermaid.listener import listener
from pagermaid.utils import Message, client, edit_delete
import requests
import time


@listener(command="liemo",
          description="调用猎魔接口查询")
async def example(_: Client, message: Message):
    args = message.text.split()
    if len(args) > 1:
        arg = args[1]
        await message.edit("正在查询请稍后")
        time.sleep(2)
        url = ''
        urlls = url + arg
        response = requests.get(urlls, verify=False)
        await message.edit(response.text)
    else:
        # 处理列表长度不足的情况
        await message.edit('未获取到参数')
