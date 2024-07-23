from core.constants import Constants
from data_collector.akshare_data_collector import AkshareDataCollector
from filter.filter_chain import FilterChain
from notification.wecom_notification import WeComNotification
from radar.base import StockRadar
from stock_favor_management.stock_favor_management import StockFavorManagement
from stock_pool.stock_pool import AmountStockPool, FavorStockPool
from filter.trading.indictor_trading_filter import IndicatorTradingFilter
# from turing_filter_for_a_stock.scorer import PriceScorer, VolumeScorer, PEScorer, SentimentScorer
# from turing_filter_for_a_stock.filter import StockFilter, get_filter
# from turing_filter_for_a_stock.voting import WeightedVotingFilter
# from turing_filter_for_a_stock.stock_favor_management import add_to_favorites, send_notification


class CCIStockRadar(StockRadar):
    def __init__(self, cci_threshold: int = 300):
        self.threshold = cci_threshold

    def startup(self):
        # 0 准备市场行情快照，获取股票代码、名称、总市值、PE、PB等指标，用于筛选股票
        market_spot_df = AkshareDataCollector().get_stock_zh_a_spot_em()
        market_spot_df = market_spot_df[Constants.SPOT_EM_COLUMNS_BASE]
        # 1、准备主股票池和其他附加股票池
        mainStockPool = FavorStockPool(
            groups=["自选股", "无雷"])  # 采集自选股中的股票信息作为股票池
        
        otherStockPools = [AmountStockPool()]  # 采集其他股票池中的股票信息作为附加股票池
        for stockPool in otherStockPools:
            symbols = stockPool.get_symbols()
            mainStockPool.add_symbols(symbols)
        df = mainStockPool.get_data_with_indictores()
        df = df.merge(market_spot_df, on="code", how="left")
        # 2、附加其他指标
        df['close_to_sma5_pct'] = (
            df['close'] - df['ema_5']).abs() / df['close']
        # 3、筛选股票，实现单独的过滤器，添加到过滤器链中即可
        filters = [
            IndicatorTradingFilter(
                indicator_name="cci_88", threshold=self.threshold, comparison_operator=">="),
            IndicatorTradingFilter(indicator_name="close_to_sma5_pct", threshold=0.05, comparison_operator="<")
        ]
        filter_chain = FilterChain(filters)
        df = filter_chain.apply(df)
        if df.shape[0] == 0:
            print("无满足条件的股票！")
        else:
            # 4、评分
            # df['score'] = PriceScorer().score(df) + VolumeScorer().score(df) + PEScorer().score(df) +
            #               SentimentScorer().score(df)
            # 5、排序
            # df = filter_chain.apply(df)
            # 6、更新费纳斯雷达自选股
            sfm = StockFavorManagement()
            sfm.add_to_group(df['code'].tolist(), group_name="斐纳斯精选")
            # 7、发送消息通知
            # print(df.columns)
            WeComNotification().send_stock_df(title=f"股票筛选结果", df=df, ganzhou_index=0.1)
