# -*- encoding: UTF-8 -*-

import data_fetcher
import settings
import strategy.enter as enter
from strategy import turtle_trade, climax_limitdown
from strategy import backtrace_ma250
from strategy import breakthrough_platform
from strategy import parking_apron
from strategy import low_backtrace_increase
from strategy import keep_increasing
from strategy import high_tight_flag
import akshare as ak
import push
import logging
import time
import datetime
from tqdm import tqdm
import settings
import json


def prepare():
    logging.info(
        f"股票池： {settings.query}")
    # all_data = ak.stock_zh_a_spot_em()
    # subset = all_data[['代码', '名称']]
    # stocks = [tuple(x) for x in subset.values]
    # statistics(all_data, stocks)
    stocks = [tuple(x) for x in settings.lhb_df.values]
    strategies = {
        '放量上涨': enter.check_volume,
        # '均线多头': keep_increasing.check,
        # '停机坪': parking_apron.check,
        # '回踩年线': backtrace_ma250.check,
        # '突破平台': breakthrough_platform.check,
        '无大幅回撤': low_backtrace_increase.check,
        '海龟交易法则': turtle_trade.check_enter,
        # '高而窄的旗形': high_tight_flag.check,
        # '放量跌停': climax_limitdown.check,
    }

    # if datetime.datetime.now().weekday() == 0:
    #     strategies['均线多头'] = keep_increasing.check

    process(stocks, strategies)

    # logging.info(
    #     "************************ process   end ***************************************")


def process(stocks, strategies):
    stocks_data = data_fetcher.run(stocks)

    pbar = tqdm(range(len(strategies.items())), desc='策略正在二次筛选中',
                bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed} < {remaining}, {rate_fmt}]', colour='blue')
    for strategy, strategy_func in strategies.items():
        check(stocks_data, strategy, strategy_func)
        pbar.update(1)  # 手动更新进度条
        time.sleep(2)


def check(stocks_data, strategy, strategy_func):
    end = settings.config['end_date']
    m_filter = check_enter(end_date=end, strategy_fun=strategy_func)
    results = dict(filter(m_filter, stocks_data.items()))
    # print(m_filter)
    # print(stocks_data)
    # print(results.columns)
    if len(results) > 0:
        results_with_zdf_amount = []
        for key, df in results.items():
            # print(df.columns)
            price = df.iloc[-1]['收盘']
            price_change = df.iloc[-1]['涨跌幅']
            amount = df.iloc[-1]['成交额']
            # new_key = (key[0], key[1], f'{price_change}%', f'{amount / 10000:.2f}万')
            new_key = (key[0], key[1],price, f'{price_change}%', amount)
            results_with_zdf_amount.append(new_key)
        sorted_results = sorted(results_with_zdf_amount,
                                key=lambda x: x[-1])[::-1]
        sorted_results = [
            (tup[0], tup[1], tup[2], tup[3], f"{tup[4] / 10000:.2f}") for tup in sorted_results]

        push.strategy('**{0}**\n{1}\n'.format(
            strategy, '\n'.join([str(item) for item in sorted_results])))
        # push.strategy('**************"{0}"**************\n{1}\n**************"{0}"**************\n'.format(strategy, '\n'.join([str(item) for item in list(results_with_zdf.keys())])))


def check_enter(end_date=None, strategy_fun=enter.check_volume):
    """
    根据设定的条件，判断某只股票是否满足买入条件。

    Args:
        end_date (datetime.date, optional): 股票数据结束日期。默认为None，表示不设置结束日期。
        strategy_fun (callable, optional): 判断买入条件的函数。默认为enter.check_volume函数。

    Returns:
        callable: 返回一个新的函数，该函数用于过滤股票数据，只保留满足条件的股票。

    """
    def end_date_filter(stock_data):
        if end_date is not None:
            if end_date < stock_data[1].iloc[0].日期:  # 该股票在end_date时还未上市
                logging.debug("{}在{}时还未上市".format(stock_data[0], end_date))
                return False
        return strategy_fun(stock_data[0], stock_data[1], end_date=end_date)

    return end_date_filter


# 统计数据
def statistics(all_data, stocks):
    limitup = len(all_data.loc[(all_data['涨跌幅'] >= 9.5)])
    limitdown = len(all_data.loc[(all_data['涨跌幅'] <= -9.5)])

    up5 = len(all_data.loc[(all_data['涨跌幅'] >= 5)])
    down5 = len(all_data.loc[(all_data['涨跌幅'] <= -5)])

    msg = "涨停数：{}   跌停数：{}\n涨幅大于5%数：{}  跌幅大于5%数：{}".format(
        limitup, limitdown, up5, down5)
    push.statistics(msg)
