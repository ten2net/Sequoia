from abc import ABC, abstractmethod

class Scorer(ABC):
    @abstractmethod
    def score(self, row):
        pass

class PriceScorer(Scorer):
    def score(self, row):
        return min(1, 1 / row['Close'])

class VolumeScorer(Scorer):
    def score(self, row):
        return row['Volume'] / 1000000

class PEScorer(Scorer):
    def score(self, row):
        return min(1, 1 / row['PE'])

class SentimentScorer(Scorer):
    def score(self, row):
        return row['Sentiment']
