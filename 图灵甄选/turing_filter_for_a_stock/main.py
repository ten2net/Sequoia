import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time
import schedule
from tqdm import tqdm
import argparse
import threading

from radar.cci_88_radar import CCIStockRadar

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
    后期维护主要工作：
    继承StockRadar，实现特定筛选策略和排序策略的金融雷达系统,
    部署到下面的数组stock_radares中，然后多线程启动每个雷达
    Args:
        无参数。    
    Returns:
        无返回值。    
    """    
    stock_radares = [
        CCIStockRadar(cci_threshold=300),
        CCIStockRadar(cci_threshold=200),
    ]
    threads = []
    for radar in stock_radares:
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
    load_dotenv()  # Load environment variables from .env file

    if args.dev:
        start_financial_radar_system()
    else:
        houres = [13, 14]
        minutes = [26, 32, 33, 35, 40, 45, 50, 55, 59]
        minutes = [45, 50, 55, 59]
        pbar_list = []
        for hour in houres:
            for minute in minutes:
                seconds_to_target = next_exec_seconds(hour, minute)

                pbar = tqdm(range(seconds_to_target), desc=f'正在等待{hour}:{minute}任务执行...',
                            bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed} < {remaining}, {rate_fmt}]', colour='yellow')

                EXEC_TIME = f"{'0' + str(hour) if hour < 10 else str(hour)}:{minute}"
                schedule.every().day.at(EXEC_TIME).do(
                    lambda: start_financial_radar_system())
                pbar_list.append(pbar)
        while True:
            schedule.run_pending()
            time.sleep(1)
            for pbar in pbar_list:
                pbar.update(1)  # 手动更新进度条

    # df = load_data()

    # adc = AkshareDataCollector()
    # df = adc.get_data('300397','20240701','20240719')
    # print(df.shape,df.columns)
    # df = adc.get_data_with_indictores('300397','20240701','20240719')
    # print(df[['macd']])
    # df = adc.get_data_with_indictores('002384')
    # print(df.shape,df.columns)
    # print(df.tail(49))
    # df = adc.get_data_with_indictores('600611')
    # print(df.shape,df.columns)
    # print(df.tail(49))
    # df = adc.get_data_with_indictores('605111')
    # print(df.shape,df.columns)
    # print(df.tail(49))
    # df = adc.get_data_with_indictores('300207')
    # print(df.shape,df.columns)
    # print(df.tail(49)[["cci_88","std" , "is_high_cc_std" , "is_high_cci" , "is_high_volume"]])

    # Get filter
    # filter = get_filter()

    # Filter critical factors
    # filtered_stocks = df
    # for filter_cls in filter:
    #     filtered_stocks = filter_cls().filter(filtered_stocks)

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
