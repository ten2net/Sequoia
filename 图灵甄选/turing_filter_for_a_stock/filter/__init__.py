from .abstract_filter import StockFilter
from .fundamental.fundamental_filter import FundamentalFilter
from .news.news_filter import NewsFilter
from .trading.indictor_trading_filter import IndicatorTradingFilter
from .others.other_filter import OtherFilter

def get_filters():
    return [FundamentalFilter, NewsFilter, IndicatorTradingFilter, OtherFilter]
