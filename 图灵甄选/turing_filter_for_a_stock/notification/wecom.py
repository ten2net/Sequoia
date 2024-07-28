from typing import List
import requests
import datetime
import os
import json
import pandas as pd

ganzhou_index_list:List[float]=[]
class WeCom:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_message(self, title: str = "甘州图灵测试", message: str = "测试消息"):
        now = datetime.datetime.now()
        formatted_now = now.strftime("%m月%d日 %H:%M")
        """发送markdown消息到企业微信群"""
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f'## <font color="comment">{title}{formatted_now}</font> \n\n {message}'
            }
        }
        response = requests.post(self.webhook_url, json=data)
        return response.json()


class WeComNotification:
    def __init__(self):
        config = json.loads(os.environ.get('WECOM_GROUP_BOT_KEYS'))
        self.wecom_group_bot_keys = [item['key'] for item in config]

    def build_markdown_msg(self, stocks_df, ganzhou_index):
        global ganzhou_index_list
        ganzhou_index_list.append(ganzhou_index)
        ganzhou_index_list = ganzhou_index_list[-3:]
        ganzhou_index_title = "情绪指数：" + "➡️".join(str(num) for num in ganzhou_index_list)
        title = "代码 简称 \n 昨收 昨天涨幅\n 最新 最新涨幅"
        stocks_df['markdown'] = stocks_df.apply(
            lambda x: f"""[{x['code']} {x['name']}](https://www.iwencai.com/unifiedwap/result?w={x['code']}&querytype=stock)"""
            + '\n <font color="info">' + f"{x['close_yestday']:.2f}  {x['pct_yestday']:.2f}%" + '</font>'
            + '\n <font color="warning">' + f"{x['close']:.2f}  {x['pct']:.2f}%" + '</font>',
            axis=1)        

        stocks_list = stocks_df['markdown'].tolist()

        return f"\n* 情绪指数(-1 ~ 1),可用来调整仓位比例\n  {ganzhou_index_title}\n\n\n{title}\n"+"\n".join(stocks_list)

    def send(self, title: str, message: str):
        for key in self.wecom_group_bot_keys:
            webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
            wecom = WeCom(webhook_url)
            response = wecom.send_message(title, message)
            print(response, f"""消息长度:{len(message)}""")

    def send_stock_df(self, title: str, df: pd.DataFrame, ganzhou_index: float):
        msg = self.build_markdown_msg(df, ganzhou_index)
        self.send(title=title, message=msg)
