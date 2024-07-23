import pandas as pd
import numpy as np
import akshare as ak
from datetime import datetime, timedelta
import time
import schedule
from tqdm import tqdm
from termcolor import colored
import argparse
import pywencai

# ==================      三角旗型突破策略     ======================
#
# 1、两市剔除ST股、剔除科创板股、剔除北交所股
# 2、9.25分按集合竞价金额降序排序，选出开盘金额最大前20只股
# 3、选出市值低于300亿的个股
# 4、剔除近20日没有涨停的股
# 5、选出前三日股价上升的个股
# 6、选出今日高开的个股
# 7、判定个股是否为近日的热点板块概念股
# 8、9.35分买入一笔
# 9、9.35分股价大于分时均线，继续买入一笔
# 10、若是快速秒板则涨停板上继续买入。
# ===================================================================


class WeCom:
    def __init__(self, webhook_url):
        self.webhook_url = webhook_url

    def send_message(self, message):
        import requests
        import datetime

        now = datetime.datetime.now()
        formatted_now = now.strftime("%m月%d日 %H:%M")
        """发送markdown消息到企业微信群"""
        data = {
            "msgtype": "markdown",
            "markdown": {
                "content": f'## <font color="comment">甘州图灵三角旗型策略{formatted_now}</font> \n\n {message}'
            }
        }
        response = requests.post(self.webhook_url, json=data)
        return response.json()


def cta_strategy(df):
    # 总市值小于700亿
    df = df.where(df['market_cap'] < 1200, np.nan).dropna(
        subset=['market_cap'])
    # 总市值大于30亿
    df = df.where(df['market_cap'] > 50, np.nan).dropna(subset=['market_cap'])

    # 前三日股价上升的个股（昨天的收盘价大于4天前的开盘价）
    df['last_3_high'] = df['close_price'] > df['last_open_4']
    df = df.where(df['last_3_high'], np.nan).dropna(
        subset=['last_3_high'])
    # print(df)
    # 昨天收盘价低于今日开盘价（今日高开）
    df['today_open_high'] = df['open_price'] > 0.7 * df['close_price']
    df = df.where(df['today_open_high'], np.nan).dropna(
        subset=['today_open_high'])
    # print(df)
    # 是否是三角旗形态
    df = df.where(df['above_support_after_rally'] == True, np.nan).dropna(
        subset=['above_support_after_rally'])
    print(df)
    # 计算集合竞价涨幅后，按涨幅从大到小排序
    df["涨幅"] = round(
        100 * (df["open_price"] - df["close_price"]) / df["close_price"], 2)

    # 是否是真突破
    df['is_true_up'] = df['pct_change'] > df['涨幅']
    df = df.where(df['is_true_up'], np.nan).dropna(
        subset=['is_true_up'])

    # 剔除长实体长上影（拉高出货）
    df['has_long_up_bar'] = df['high_close'] <= df['close_open']
    df = df.where(df['has_long_up_bar'], np.nan).dropna(
        subset=['has_long_up_bar'])
    # 剔除现价小于开盘价的
    df['is_red_line'] = df['close_open'] >= 0.005
    df = df.where(df['is_red_line'], np.nan).dropna(
        subset=['is_red_line'])

    df = df[["code", "name", "close_price", "open_price",
             "涨幅", "pct_change", 'current_price']]
    df.sort_values(by='pct_change', ascending=False, inplace=True)

    return df

# 定义获取股票数据的函数


def get_stock_data(stock_code):
    # stock_code="002600"
    window = 60
    start_date = datetime.now() - timedelta(days=2 * window)
    start_date_str = start_date.strftime('%Y%m%d')
    df = ak.stock_zh_a_hist(
        symbol=stock_code, start_date=start_date_str, adjust='')
    df['pct_change'] = df['收盘'].pct_change(periods=1)  # 计算百分比变化

    # 新股特殊处理，防止报错
    last_close = df.iloc[-1]['开盘']
    today_open = df.iloc[-1]['开盘']
    last_open_4 = df.iloc[-1]['开盘']

    if len(df) > 4:  # 非新股特殊处理
        last_close = df.iloc[-2]['收盘']
        today_open = df.iloc[-1]['开盘']
        # 获取前三日的开盘价
        last_open_4 = df.iloc[-4]['开盘']

    pct_change = df.iloc[-1]['涨跌幅']
    high_close = (df.iloc[-1]['最高'] - df.iloc[-1]['收盘']) / df.iloc[-1]['收盘']
    close_open = (df.iloc[-1]['收盘'] - df.iloc[-1]['开盘']) / df.iloc[-1]['开盘']
    current_price = df.iloc[-1]['收盘']

    # 旗型处理
    df['MA'] = df['收盘'].rolling(window=window).mean()
    df['Above_MA'] = (df['收盘'] > df['MA']).astype(int)
    # print(df)
    recent_days = df['pct_change'].tail(13)

    max_pct_change_idx = recent_days.idxmax()
    max_pct_change = df.loc[max_pct_change_idx, 'pct_change']
    max_pct_change_date = df.loc[max_pct_change_idx, '日期']
    max_pct_change_date_low = df.loc[max_pct_change_idx, '最低']
    high_close_bar = df.loc[max_pct_change_idx,
                            '最高'] - df.loc[max_pct_change_idx, '收盘']
    close_open_bar = df.loc[max_pct_change_idx,
                            '收盘'] - df.loc[max_pct_change_idx, '开盘']
    no_long_up_bar = high_close_bar < 0.8 * close_open_bar  # 无冲高回落形态
    # 从那一天开始，找到所有后续交易日的最低价，使用布尔索引来选择那一天之后的所有日期
    mask = df['日期'] >= max_pct_change_date
    min_low_after = df.loc[mask, '最低'].min()
    # 计算交易日数量
    trading_days_after = df.loc[mask]
    trading_days_count = trading_days_after.shape[0]

    Above_MA = df.loc[df.index[-1], 'Above_MA']
    # 最近一次大涨后，接下来的交易日是否跌穿过大涨当日的最低价
    Above_MA = df.loc[df.index[-1], 'Above_MA']
    above_support_after_rally = max_pct_change >= 0.09 \
      and no_long_up_bar \
        and Above_MA == 1 \
          and trading_days_count > 3 \
            and trading_days_count < 12 \
              and min_low_after >= max_pct_change_date_low

    # 获取总市值和行业
    stock_info = ak.stock_individual_info_em(symbol=stock_code)
    market_cap = stock_info.iloc[0]['value'] / (10000 * 10000)  # 总市值
    stock_name = stock_info.iloc[5]['value']  # 股票简称
    # item          value
    # 0   总市值  55740263855.5
    # 1  流通市值  55740263855.5
    # 2    行业            半导体
    # 3  上市时间       20030603
    # 4  股票代码         600584
    # 5  股票简称           长电科技
    # 6   总股本   1789414570.0
    # 7   流通股   1789414570.0

    return {
        'code': stock_code,
        'name': stock_name,
        'market_cap': market_cap,
        'close_price': last_close,
        'open_price': today_open,
        'last_open_4': last_open_4,
        'pct_change': pct_change,
        'above_support_after_rally': above_support_after_rally,
        'high_close': high_close,
        'close_open': close_open,
        'current_price': current_price
    }


def build_markdown_msg(stocks_df):
    stocks_df['markdown'] = stocks_df[['code', 'close_price', 'current_price', '涨幅', 'name', 'pct_change']].apply(
        lambda x: f"""[{x[0]} {x[4]}](https://www.iwencai.com/unifiedwap/result?w={x[0]}&querytype=stock)"""
        + ' <font color="warning">' + f"{x[2]:.2f}" + '</font>'
        + ' <font color="comment">' + f"{x[3]:.2f}%" + '</font>'
        + f" {x[5]:.2f}%", axis=1)

    stocks_df['markdown'] = stocks_df['markdown'].astype(str)
    stocks_list = stocks_df['markdown'].tolist()
    return f"\n代码 简称 现价 涨幅开 涨幅现\n"+"\n".join(stocks_list)


def is_trading_time():
    from datetime import datetime, time
    now = datetime.now()
    work_start_1 = time(9, 32)
    work_end_1 = time(11, 32)
    work_start_2 = time(13, 15)
    work_end_2 = time(15, 1)

    # 判断是否为工作日（周一到周五）
    if now.weekday() < 5:  # 0是周一，4是周五
        # 判断当前时间是否在上班时间内
        if work_start_1 <= now.time() <= work_end_1:
            return True
        if work_start_2 <= now.time() <= work_end_2:
            return False  # 下午不交易
    return False


def get_top_30_deal_volume_stocks(pbar=None):
    from datetime import datetime, time
    if is_trading_time():
        df = ak.stock_zh_a_spot_em()
        try:
            # 两市剔除ST股、剔除科创板股、剔除北交所股
            df = df[~df['代码'].astype(str).str.startswith('4')]
            df = df[~df['代码'].astype(str).str.startswith('8')]
            df = df[~df['代码'].astype(str).str.startswith('68')]
            df = df[~df['名称'].astype(str).str.startswith('N')]
            df = df[~df['名称'].astype(str).str.startswith('*')]
            df = df[~df['名称'].astype(str).str.startswith('ST')]
            # 按成交额降序排序，选出开盘金额最大前N只股
            df = df.sort_values(by='成交额', ascending=False)
            df = df.head(400)
            stock_codes = df['代码'].to_list()
            stock_codes = [item[:6] for item in stock_codes]
            data = [get_stock_data(code) for code in stock_codes]

            # 运行策略函数
            df = pd.DataFrame(data)
            selected_stocks = cta_strategy(df)
            if len(selected_stocks) < 1:
                return
            msg = build_markdown_msg(selected_stocks)
            keys = [
                '88aa58e5-818a-471d-8786-84ee85984467',
                'e312ad13-1f18-430b-9c66-304922694dc3'
            ]
            for key in keys:
                webhook_url = f"https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={key}"
                wecom = WeCom(webhook_url)
                response = wecom.send_message(msg)
        except Exception as e:
            print(repr(e), df)

    if pbar:
        seconds_to_target = 3 * 60
        pbar.reset(seconds_to_target)


def next_exec_seconds(hour=9, minute=41):
    now = datetime.now()
    target_time = datetime(now.year, now.month, now.day, hour, minute)
    if now >= target_time:
        target_time += timedelta(days=1)
    time_difference = target_time - now
    seconds_to_target = round(time_difference.total_seconds())
    return seconds_to_target


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="处理命令行参数")
    parser.add_argument('--dev', action='store_true',
                        help='Set dev mode to true')
    args = parser.parse_args()

    if args.dev:
        get_top_30_deal_volume_stocks()
    else:
        hour = 9
        minute = 41
        seconds_to_target = next_exec_seconds(hour, minute)
        seconds_to_target = 3 * 60
        pbar = tqdm(range(seconds_to_target), desc='正在等待任务执行...',
                    bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed} < {remaining}, {rate_fmt}]', colour='yellow')

        # EXEC_TIME = f"{'0' + str(hour) if hour < 10 else str(hour)}:{minute}"
        # schedule.every().day.at(EXEC_TIME).do(
        #     lambda: get_top_30_deal_volume_stocks(pbar))
        schedule.every(3).minutes.do(
            lambda: get_top_30_deal_volume_stocks(pbar))
        while True:
            schedule.run_pending()
            time.sleep(1)
            pbar.update(1)  # 手动更新进度条
