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

logging.basicConfig(format='## %(asctime)s %(message)s',datefmt='%Y-%m-%d %H:%M', filename='选票结果.md')
logging.getLogger().setLevel(logging.INFO)
# industry_queries 用来动态给stock_queries添加股票池查询
industry_queries=['今日涨跌幅大于0.5，且涨跌幅排名前8的行业', '技术面评分排名前3名的行业板块']
# 固定的股票池查询
stock_queries = [
    '高位阳包阴并创新高的非ST、非科创板的未涨停股票',
    '换手率排名前100，技术形态为价升量涨的非ST、非科创板的未涨停股票',
    '流通市值大于100亿且成交金额最近连续两个交易日排名前100名的未涨停股票'
]  

pbar = None

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
    queries=['今日涨跌幅大于0.5，且涨跌幅排名前8的行业', '技术面评分排名前3名的行业板块']
    for query in queries:
        df = pywencai.get(query=query,query_type="zhishu")
        results =df['指数简称'].to_list()
        dynamic_queries += [f'技术面评分排名前10的非ST、非科创板{industry_sector}行业未涨停股票' for industry_sector in results ]
    return dynamic_queries
    
def job():
    if utils.is_weekday():
        queries = gen_dynamic_query() + stock_queries
        for stock_query in queries:
            settings.init(stock_query)           
            work_flow.prepare()            
    pbar.reset()          

if __name__ == '__main__':
    tips = f'{"=" * 50}\n提示: 请查看文件\n{Path.cwd() / "选票结果.md"}\n{"=" * 50}'
    print(colored(tips,'magenta'))  
    settings.init()  
    if settings.config['cron'] and is_trading_time():
        # EXEC_TIME = "15:15"
        # schedule.every().day.at(EXEC_TIME).do(job)
        schedule.every(settings.config['cron_period']).minutes.do(job) 
        
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
