from turing_filter_for_a_stock.scorer import Scorer, PriceScorer, VolumeScorer, PEScorer, SentimentScorer
import pandas as pd

class WeightedVotingFilter:
    def __init__(self, scorer, weights):
        self.scorer = {scorer.__name__.lower(): scorer for scorer in scorer}
        self.weights = weights

    def filter(self, df):
        for scorer_name, scorer in self.scorer.items():
            df[scorer_name] = df.apply(scorer().score, axis=1)
        
        df['Total Score'] = df[list(self.weights.keys())].dot(self.weights.values)
        return df.sort_values(by='Total Score', ascending=False)
