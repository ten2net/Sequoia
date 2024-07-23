from ..abstract_filter import StockFilter

class FundamentalFilter(StockFilter):
    def filter(self, df):
        # Example: Filter stocks with PE ratio less than 20
        return df[df['PE'] < 20]
