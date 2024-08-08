import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import schedule
from tqdm import tqdm
import argparse
import threading
from config import stock_radares,jinjia_stock_radares,dev_stock_radares
from radar.hot_symbols import HotSymbolStockRadar
from radar.jingjia_rise_event import JingJiaRiseStockRadar
from trader.trader_management import SimTraderManagement

def next_exec_seconds(hour=9, minute=26):
    now = datetime.now()
    target_time = datetime(now.year, now.month, now.day, hour, minute)
    if now >= target_time:
        target_time += timedelta(days=1)
    time_difference = target_time - now
    seconds_to_target = round(time_difference.total_seconds())
    return seconds_to_target


def start_financial_radar_system():
    """
    启动金融雷达系统。股票池、选股、评分、排序、添加到自选、发送企业微信等消息通知等功能全部在继承自StockRadar类的
    雷达系统中实现。
    Args:
        无参数。    
    Returns:
        无返回值。    
    """    
    threads = []
    for radar in stock_radares:
        thread = threading.Thread(target=radar.startup)
        thread.start()  # 启动线程
        threads.append(thread)
    # 等待所有线程完成
    for thread in threads:
        thread.join()  
def start_jingjia_rice_radar():
    threads = []
    for radar in jinjia_stock_radares:
        thread = threading.Thread(target=radar.startup)
        thread.start()  # 启动线程
        threads.append(thread)
    # 等待所有线程完成
    for thread in threads:
        thread.join()    
def start_dev_radar():
    threads = []
    for radar in dev_stock_radares:
        thread = threading.Thread(target=radar.startup)
        thread.start()  # 启动线程
        threads.append(thread)
    # 等待所有线程完成
    for thread in threads:
        thread.join()    
    
def main():
    parser = argparse.ArgumentParser(description="处理命令行参数")
    parser.add_argument('--dev', action='store_true',
                        help='Set dev mode to true')
    args = parser.parse_args()
    # load_dotenv()  # Load environment variables from .env file
    os.environ.pop("EM_APPKEY")
    os.environ.pop("EM_HEADER")
    os.environ.pop("WECOM_GROUP_BOT_KEYS")       
    load_dotenv() 
    
    stm = SimTraderManagement()  # 模拟交易管理
    stm.startWatch()      

    if args.dev:
        start_dev_radar()
    else:
        pbar_list = []
        task_cron_config=[
            ([9],[26,28,31],[start_dev_radar]),
            ([9],[30 + i * 2 for i in range(29 // 2 + 1)],[start_dev_radar]),
            ([11],[i * 3 for i in range(30 // 3 + 1)],[start_dev_radar]),
            ([10,13,14],[i * 3 for i in range(59 // 3 + 1)],[start_dev_radar]),
        ]
        for cron_config in task_cron_config:
            hours = cron_config[0]
            minutes = cron_config[1]
            functions = cron_config[2]
            for hour in hours:
                for minute in minutes:
                    seconds_to_target = next_exec_seconds(hour, minute)
                    hour_str = f"{'0' + str(hour) if hour < 10 else str(hour)}"
                    minute_str = f"{'0' + str(minute) if minute < 10 else str(minute)}"
                    
                    pbar = tqdm(range(seconds_to_target), desc=f'正在等待{hour}:{minute_str}任务执行...',
                            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed} < {remaining}, {rate_fmt}]', colour='yellow')
                    EXEC_TIME = f"{hour_str}:{minute_str}"
                    schedule.every().day.at(EXEC_TIME).do(
                                    lambda: [func() for func in functions])
                    pbar_list.append(pbar)
        
        while True:
            schedule.run_pending()
            time.sleep(1)
            for pbar in pbar_list:
                pbar.update(1)  # 手动更新进度条

    # # Define non-critical factors' scorer and weights
    # scorer = [PriceScorer, VolumeScorer, PEScorer, SentimentScorer]
    # weights = {
    #     'price': 0.3,
    #     'volume': 0.2,
    #     'pe': 0.3,
    #     'sentiment': 0.2
    # }

    # # Create weighted voting filter
    # voting_filter = WeightedVotingFilter(scorer, weights)


    # # Filter non-critical factors
    # final_filtered_stocks = voting_filter.filter(filtered_stocks)
    # # Add to favorites
    # add_to_favorites(final_filtered_stocks)
    # # Send notification
    # send_notification(final_filtered_stocks)
if __name__ == "__main__":
    main()
