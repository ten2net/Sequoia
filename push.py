# -*- encoding: UTF-8 -*-

import logging
import settings
from wxpusher import WxPusher
import requests 

class WeCom:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_message(self, message):
        """发送markdown消息到企业微信群"""
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f'<font color="warning">{settings.query}</font> \n\n {message}'
            }
        }
        response = requests.post(self.webhook_url, json=data)
        return response.json()
def push(msg):
    if settings.config['push']['enable']:
        # response = WxPusher.send_message(msg, uids=[settings.config['push']['wxpusher_uid']],
        #                                  token=settings.config['push']['wxpusher_token'])
        # print(response)
        keys=[
            '88aa58e5-818a-471d-8786-84ee85984467',
            'e312ad13-1f18-430b-9c66-304922694dc3'
        ]
        for key in keys:
            webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
            wecom = WeCom(webhook_url)
            response = wecom.send_message(msg)
            # print(response)
        logging.info(msg, extra={'h': 3})


def statistics(msg=None):
    push(msg)


def strategy(msg=None):
    if msg is None or not msg:
        msg = '今日没有符合条件的股票'
    push(msg)
