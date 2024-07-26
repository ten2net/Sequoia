from radar.cci_88 import CCIStockRadar
# from radar.del_test import DelTest
from radar.large_buy_event import LargeBuyStockRadar
from radar.ta_kline_style import KLineStyleStockRadar
# 后期维护主要工作：
# 继承StockRadar，实现特定筛选策略和排序策略的金融雷达系统,
# 部署到下面的数组stock_radares中，然后多线程启动每个雷达
stock_radares = [
    # DelTest(name="斐纳斯强势300", cci_threshold=250),
    # CCIStockRadar(name="斐纳斯强势300", cci_threshold=250),
    # KLineStyleStockRadar(name="K线异常", threshold=0, topN =200),
    # CCIStockRadar(name="斐纳斯强势300", cci_threshold=250),
    LargeBuyStockRadar(name="大笔买入", topN =22),
]