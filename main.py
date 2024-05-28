# -*- encoding: UTF-8 -*-

import utils
import logging
import work_flow
import settings
import schedule
import time
import datetime
from pathlib import Path
from tqdm import tqdm

logging.basicConfig(format='%(asctime)s %(message)s', filename='sequoia.log')
logging.getLogger().setLevel(logging.INFO)
stock_queries = [
    '高位跳空低开',
    'boll线上穿中轨，且换手率<4%',
    '高位低开，且换手率<4%',
    '高位阳包阴并创新高',
    '近5日两融净流入大于1亿，K线形态为反包',
    '近5日两融净流入大于1亿，K线形态为射击之星',
    '今日10点02分之前，成交额大于2亿且15分钟线突破前高的上升通道',
    '总市值大于100亿且成交金额最近连续两个交易日排名前100名',
    '现金储备排名前50，股价突破60日均线'
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
def job():
    if utils.is_weekday():
        for stock_query in stock_queries:
            settings.init(stock_query)           
            work_flow.prepare()            
    pbar.reset()          
            

if __name__ == '__main__':
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
        for stock_query in stock_queries:
            settings.init(stock_query)            
            work_flow.prepare()
