import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import schedule
from tqdm import tqdm
import argparse
import threading
from config import stock_radares,jinjia_stock_radares
from trader.trader_management import SimTraderManagement
from user.user_management import UserManagement

def is_trading_time(now):
    """
    检查当前时间是否在交易时段内。
    交易时段为每个交易日的9:26到15:00。
    """
    start_hour_9 = 9
    start_minute = 26
    
    end_hour_11 = 11
    start_hour_13 = 13
    end_hour_15 = 15
    # 构建交易开始和结束的时间
    start_1 = datetime(now.year, now.month, now.day, start_hour_9, start_minute)
    end_1 = datetime(now.year, now.month, now.day, end_hour_11, 30)
    
    start_2 = datetime(now.year, now.month, now.day, start_hour_13, 0)
    end_2 = datetime(now.year, now.month, now.day, end_hour_15, 0)
    
    return now.weekday() < 5 and ((start_1 <= now <= end_1) or (start_2 <= now <= end_2))

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
    now = datetime.now()  
    if not is_trading_time(now):return
    threads = []
    for radar in stock_radares:
        thread = threading.Thread(target=radar.startup)
        thread.start()  # 启动线程
        threads.append(thread)
    # 等待所有线程完成
    for thread in threads:
        thread.join()  
def task_for_del_all_from_group():
    """
    清空几个重要自选股分组。
    Args:
        无参数。    
    Returns:
        无返回值。    
    """ 
    now = datetime.now()  
    # if not is_trading_time(now):return    
    groups= ["封神榜全榜","大笔买全榜","每日情全榜","热股强全榜","买信号全榜","卖信号全榜"]
    um = UserManagement()
    for user in um.users:
        for group_name in groups:
            user.favor.del_all_from_group(group_name=group_name)
 
def start_jingjia_rice_radar():
    now = datetime.now()  
    if not is_trading_time(now):return    
    threads = []
    for radar in jinjia_stock_radares:
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
    os.environ.pop("USER_CONFIG_LIST")
    os.environ.pop("ACCOUNT_STRATEGT_MAPPING")
    os.environ.pop("WECOM_GROUP_BOT_KEYS")   
   
    load_dotenv() 
    um = UserManagement()  # 启动用户的自选股更新信号侦听
    um.startWatch()    
    stm = SimTraderManagement()  # 启动模拟账户的模拟交易信号侦听
    stm.startWatch()      

    if args.dev:
        start_jingjia_rice_radar()
        # start_financial_radar_system()
    else:
        pbar_list = []
        task_cron_config=[
            ([9],[10],[task_for_del_all_from_group]), # 自选股全榜中删除前一天的出票
            ([9],[26,28,31],[start_jingjia_rice_radar]),
            ([9],[30 + i * 2 for i in range(29 // 2 + 1)],[start_financial_radar_system]),
            ([11],[i * 3 for i in range(30 // 3 + 1)],[start_financial_radar_system]),
            ([10,13,14],[i * 3 for i in range(59 // 3 + 1)],[start_financial_radar_system]),
            ([22],[30],[start_financial_radar_system]),
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

if __name__ == "__main__":
    main()
