# -*- encoding: UTF-8 -*-

import utils
import logging
import work_flow
import settings
import schedule
import time
import datetime
from pathlib import Path
import pywencai
from tqdm import tqdm
from termcolor import colored
import pandas as pd
import ast
import requests
import csv

logging.basicConfig(format='## %(asctime)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M', filename='选票结果.md')
logging.getLogger().setLevel(logging.INFO)

# 固定的股票池查询
stock_queries = [
    # '高位阳包阴并创新高的非ST、非科创板的未涨停股票'
]


class WeCom:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_message(self, message):
        now = datetime.datetime.now()
        formatted_now = now.strftime("%m月%d日 %H:%M")
        """发送markdown消息到企业微信群"""
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f'## <font color="warning">甘州图灵封神榜{formatted_now}</font> \n\n {message}'
            }
        }
        response = requests.post(self.webhook_url, json=data)
        return response.json()


def push(msg):
    if settings.config['push']['enable']:
        keys = [
            '88aa58e5-818a-471d-8786-84ee85984467',
            'e312ad13-1f18-430b-9c66-304922694dc3'
        ]
        for key in keys:
            webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
            wecom = WeCom(webhook_url)
            response = wecom.send_message(msg)


pbar = None
leaderboard_today = []


def is_trading_time():
    now = datetime.datetime.now()
    work_start_1 = datetime.time(9, 20)
    work_end_1 = datetime.time(11, 30)
    work_start_2 = datetime.time(13, 0)
    work_end_2 = datetime.time(15, 0)

    # 判断是否为工作日（周一到周五）
    if now.weekday() < 5:  # 0是周一，4是周五
        # 判断当前时间是否在上班时间内
        if work_start_1 <= now.time() <= work_end_1:
            return True
        if work_start_2 <= now.time() <= work_end_2:
            return True
    return False


def gen_dynamic_query():
    dynamic_queries = []
    queries = [
        '今日涨跌幅大于0.5，且涨跌幅排名前3的行业',
        '今日涨跌幅大于0.5，且资金净流入排名前3的行业',
        '三日区间涨幅大于2.5%的行业板块'
    ]
    results = []
    for query in queries:
        df = pywencai.get(query=query, query_type="zhishu")
        if df is not None:
            results += df['指数简称'].to_list()
    results = list(set(results))
    if len(results) > 0:
        # dynamic_queries += [f'技术面评分排名前10的非ST、非科创板{industry_sector}行业未涨停股票' for industry_sector in results ]
        dynamic_queries += [
            f'流通市值大于100亿且成交金额排名前100名的{industry_sector}行业未涨停股票' for industry_sector in results]
        dynamic_queries += [
            f'换手率排名在20到100之间，技术形态为价升量涨的非ST、非科创板的{industry_sector}行业未涨停股票' for industry_sector in results]
    return dynamic_queries


def job(leaderboard_today):
    if utils.is_weekday() and is_trading_time():
        leaderboard = []
        queries = gen_dynamic_query() + stock_queries
        for stock_query in queries:
            settings.init(stock_query)
            work_flow.prepare()
            leaderboard += settings.leaderboard
        leaderboard_today += leaderboard
        # 保存封神榜数据以便后期分析
        append_leaderboard_to_file(leaderboard) 
        # 生成markdown格式的封神榜             
        leaderboard_markdown = rebuild_leaderboard_markdown(
            leaderboard)  # 剔除重复股票，并排序
        if len(leaderboard_markdown) > 0:
            push(leaderboard_markdown)
    pbar.reset()


def rebuild_leaderboard_markdown(leaderboard):
    if len(leaderboard) > 0:
        for item in leaderboard:
            current = ast.literal_eval(item['当前行情'])
            current_change = float(current[3][:-1])
            first_listed_change = current_change
            if len(leaderboard_today) > 0:
                first_match = next(
                    (row for row in leaderboard_today if row['股票代码'] == item['股票代码']), None)
                if first_match:
                    first_listed_change = float(
                        ast.literal_eval(first_match['当前行情'])[3][:-1])
                item['初榜涨幅差'] = (current_change - first_listed_change)
                # 求与上一榜的涨幅差
                second_to_last_change = current_change
                matches = [
                    row for row in leaderboard_today if row['股票代码'] == item['股票代码']]
                if len(matches) >= 2:
                    second_to_last_match = matches[-2]
                    second_to_last_change = float(ast.literal_eval(
                        second_to_last_match['当前行情'])[3][:-1])
                item['榜间涨幅差'] = (current_change - second_to_last_change)

        df_leaderboard = pd.DataFrame(leaderboard)
        # print("leaderboard_today:", leaderboard_today)

        df_leaderboard = df_leaderboard.groupby('股票代码').apply(
            lambda x: x[x.groupby('股票代码').cumcount() == (x.groupby('股票代码').cumcount().max())])
        df_leaderboard.reset_index(drop=True, inplace=True)
        df_leaderboard['当前行情'] = df_leaderboard['当前行情'].apply(
            lambda item: f"""[{item[1:-1].replace("'", "").replace(",", " ")}](https://www.iwencai.com/unifiedwap/result?w={ast.literal_eval(item)[0]}&querytype=stock)""")
        df_leaderboard = df_leaderboard[['当前行情', '初榜涨幅差', '榜间涨幅差']]
        df_sorted = df_leaderboard.sort_values(by='榜间涨幅差', ascending=False)
        df_sorted['Combined'] = df_sorted[['当前行情', '初榜涨幅差', '榜间涨幅差']].apply(
            lambda x: x[0] + ' <font color="warning">' + f"{x[1]:.2f}" + '</font>' + ' <font color="comment">' + f"{x[2]:.2f}" + '</font>', axis=1)
        df_sorted['Combined'] = df_sorted['Combined'].astype(str)
        leaderboard_list = df_sorted['Combined'].tolist()
        return "\n".join(leaderboard_list)
    else:
        return ''

def append_leaderboard_to_file(leaderboard):
    # 打开文件，追加模式 ('a')，如果文件不存在，将会自动创建
    filename = 'data/leaderboard/leaderboard.csv'
    with open(filename, 'a', newline='') as file:
        # 创建 CSV writer 对象
        writer = csv.writer(file)
        
        # 遍历 leaderboard 列表
        for row in leaderboard:
            # 获取当前时间，并格式化为字符串
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            # 将当前时间添加到元组的开头
            new_row = (current_time,) +  ast.literal_eval(row['当前行情'])                
            date_time, stock_code, stock_name, price, change_percent, turnover = new_row
            change_percent = change_percent.rstrip('%')
            new_row = (date_time, stock_code, stock_name, price, change_percent, turnover)                
            # 将新的元组写入 CSV 文件
            writer.writerow(new_row)      

if __name__ == '__main__':
    tips = f'{"=" * 50}\n提示: 请查看文件\n{Path.cwd() / "选票结果.md"}\n{"=" * 50}'
    print(colored(tips, 'magenta'))
    leaderboard = []
    settings.init()
    if settings.config['cron']:
        # EXEC_TIME = "15:15"
        # schedule.every().day.at(EXEC_TIME).do(job)
        schedule.every(settings.config['cron_period']).minutes.do(
            lambda: job(leaderboard_today))

        pbar = tqdm(range(settings.config['cron_period'] * 60), desc='正在等待任务执行...',
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed} < {remaining}, {rate_fmt}]', colour='yellow')

        while True:
            schedule.run_pending()
            time.sleep(1)
            pbar.update(1)  # 手动更新进度条
    else:
        queries = gen_dynamic_query() + stock_queries
        for stock_query in queries:
            settings.init(stock_query)
            work_flow.prepare()
            leaderboard += settings.leaderboard
        leaderboard_today += leaderboard
        # 保存封神榜数据以便后期分析
        append_leaderboard_to_file(leaderboard) 
        # 生成markdown格式的封神榜     
        leaderboard_markdown = rebuild_leaderboard_markdown(
            leaderboard)  # 剔除重复股票，并排序
        if len(leaderboard_markdown) > 0:
            push(leaderboard_markdown)
