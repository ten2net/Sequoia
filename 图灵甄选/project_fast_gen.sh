#!/bin/bash

# 创建目录结构
mkdir -p turing_filter_for_a_stock/scorer
mkdir -p turing_filter_for_a_stock/filter/fundamental
mkdir -p turing_filter_for_a_stock/filter/news
mkdir -p turing_filter_for_a_stock/filter/trading
mkdir -p turing_filter_for_a_stock/filter/others
mkdir -p turing_filter_for_a_stock/voting
mkdir -p turing_filter_for_a_stock/stock_favor_management 
mkdir -p turing_filter_for_a_stock/notification 
mkdir -p turing_filter_for_a_stock/tests
mkdir -p turing_filter_for_a_stock/datasource
mkdir -p turing_filter_for_a_stock/stock_pool
mkdir -p turing_filter_for_a_stock/local_data
mkdir -p turing_filter_for_a_stock/local_results

# 创建文件
touch turing_filter_for_a_stock/.env
touch turing_filter_for_a_stock/README.md
touch turing_filter_for_a_stock/requirements.txt
touch turing_filter_for_a_stock/.gitignore
touch turing_filter_for_a_stock/__init__.py
touch turing_filter_for_a_stock/main.py
touch turing_filter_for_a_stock/scorer/__init__.py
touch turing_filter_for_a_stock/scorer/scorer.py
touch turing_filter_for_a_stock/filter/__init__.py
touch turing_filter_for_a_stock/filter/abstract_filter.py
touch turing_filter_for_a_stock/filter/fundamental/__init__.py
touch turing_filter_for_a_stock/filter/fundamental/fundamental_filter.py
touch turing_filter_for_a_stock/filter/news/__init__.py
touch turing_filter_for_a_stock/filter/news/news_filter.py
touch turing_filter_for_a_stock/filter/trading/__init__.py
touch turing_filter_for_a_stock/filter/trading/trading_filter.py
touch turing_filter_for_a_stock/filter/others/__init__.py
touch turing_filter_for_a_stock/filter/others/other_filter.py
touch turing_filter_for_a_stock/voting/__init__.py
touch turing_filter_for_a_stock/voting/voting.py
touch turing_filter_for_a_stock/stock_favor_management/__init__.py
touch turing_filter_for_a_stock/stock_favor_management/stock_favor_management.py
touch turing_filter_for_a_stock/notification/__init__.py
touch turing_filter_for_a_stock/notification/notifications.py
touch turing_filter_for_a_stock/datasource/__init__.py
touch turing_filter_for_a_stock/datasource/datasource.py
touch turing_filter_for_a_stock/stock_pool/__init__.py
touch turing_filter_for_a_stock/stock_pool/stock_pool.py
touch turing_filter_for_a_stock/tests/__init__.py
touch turing_filter_for_a_stock/tests/test_main.py

# 添加基本文件内容
cat > turing_filter_for_a_stock/README.md << EOF
# Stock Filter Project

This project is designed to filter and sort stocks based on various criteria using a combination of critical filter and weighted voting.

## Setup

1. Clone the repository
2. Create a \`.env\` file with necessary environment variables
3. Run \`python main.py\` to start the application

## Modules

- \`scorer/\`: Contains all the scoring logic for different stock attributes.
- \`filter/\`: Contains critical filter organized by type.
- \`voting/\`: Contains the weighted voting logic for non-critical factors.
- \`stock_favor_management/\`: Manages the stocks in the stock pool and favorites, and handles notifications.

## Usage

Refer to the \`main.py\` file for usage examples.
EOF

cat > turing_filter_for_a_stock/requirements.txt << EOF
pandas==1.3.4
python-dotenv==0.19.2
requests==2.26.0
pytest==6.2.5
EOF

cat > turing_filter_for_a_stock/.gitignore << EOF
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# Distribution / packaging
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
.python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform wheels, pipenv may install dependencies in a virtualenv located in
#   the project root (as of 2018-01-26, see discussion in pypa/pipenv#984).
#   Therefore, do not include the virtualenv content in the repository.
#Pipfile.lock
#venv/
#ENV/

# PEP 582; used by e.g. github.com/David-OConnor/pyflow
__pypackages__/

# Celery
celerybeat-schedule
celerybeat.pid

# SageMath parsed files
*.sage.py

# Environments
.env
EOF

cat > turing_filter_for_a_stock/main.py << EOF
import os
import pandas as pd
from dotenv import load_dotenv

from turing_filter_for_a_stock.scorer import PriceScorer, VolumeScorer, PEScorer, SentimentScorer
from turing_filter_for_a_stock.filter import StockFilter, get_filter
from turing_filter_for_a_stock.voting import WeightedVotingFilter
from turing_filter_for_a_stock.stock_favor_management import add_to_favorites, send_notification

def load_data():
    data = {
        'Open': [150, 200, 300],
        'High': [155, 210, 310],
        'Low': [145, 190, 290],
        'Close': [150, 200, 300],
        'Volume': [100000, 50000, 200000],
        'PE': [15, 20, 10],
        'Sentiment': [0.8, 0.6, 0.9]
    }
    return pd.DataFrame(data)

def main():
    load_dotenv()  # Load environment variables from .env file
    
    df = load_data()
    
    # Get filter
    filter = get_filter()
    
    # Filter critical factors
    filtered_stocks = df
    for filter_cls in filter:
        filtered_stocks = filter_cls().filter(filtered_stocks)
    
    # Define non-critical factors' scorer and weights
    scorer = [PriceScorer, VolumeScorer, PEScorer, SentimentScorer]
    weights = {
        'price': 0.3,
        'volume': 0.2,
        'pe': 0.3,
        'sentiment': 0.2
    }
    
    # Create weighted voting filter
    voting_filter = WeightedVotingFilter(scorer, weights)
    
    # Filter non-critical factors
    final_filtered_stocks = voting_filter.filter(filtered_stocks)
    
    # Add to favorites
    add_to_favorites(final_filtered_stocks)
    
    # Send notification
    send_notification(final_filtered_stocks)

if __name__ == "__main__":
    main()
EOF

cat > turing_filter_for_a_stock/filter/abstract_filter.py << EOF
from abc import ABC, abstractmethod

class StockFilter(ABC):
    @abstractmethod
    def filter(self, df):
        pass
EOF

cat > turing_filter_for_a_stock/filter/fundamental/fundamental_filter.py << EOF
from ..abstract_filter import StockFilter

class FundamentalFilter(StockFilter):
    def filter(self, df):
        # Example: Filter stocks with PE ratio less than 20
        return df[df['PE'] < 20]
EOF

cat > turing_filter_for_a_stock/filter/news/news_filter.py << EOF
from ..abstract_filter import StockFilter

class NewsFilter(StockFilter):
    def filter(self, df):
        # Example: Filter stocks with positive news sentiment
        return df[df['News Sentiment'] > 0]
EOF

cat > turing_filter_for_a_stock/filter/trading/trading_filter.py << EOF
from ..abstract_filter import StockFilter

class TradingFilter(StockFilter):
    def filter(self, df):
        # Example: Filter stocks with volume greater than 100000
        return df[df['Volume'] > 100000]
EOF

cat > turing_filter_for_a_stock/filter/others/other_filter.py << EOF
from ..abstract_filter import StockFilter

class OtherFilter(StockFilter):
    def filter(self, df):
        # Example: Filter stocks with a specific pattern
        return df[df['Pattern'] == 'Specific']
EOF

cat > turing_filter_for_a_stock/filter/__init__.py << EOF
from .abstract_filter import StockFilter
from .fundamental.fundamental_filter import FundamentalFilter
from .news.news_filter import NewsFilter
from .trading.trading_filter import TradingFilter
from .others.other_filter import OtherFilter

def get_filter():
    return [FundamentalFilter, NewsFilter, TradingFilter, OtherFilter]
EOF

cat > turing_filter_for_a_stock/scorer/scorer.py << EOF
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
EOF

cat > turing_filter_for_a_stock/voting/voting.py << EOF
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
EOF

cat > turing_filter_for_a_stock/stock_favor_management/stock_favor_management.py << EOF
def add_to_favorites(df):
    favorites = []
    for index, row in df.iterrows():
        favorites.append({
            'Name': row['Name'],
            'Score': row['Total Score']
        })
    print("Favorites:", favorites)
EOF

cat > turing_filter_for_a_stock/stock_favor_management/notifications.py << EOF
import os
import requests

def send_notification(df):
    webhook_url = os.getenv("WEBHOOK_URL")
    message = "Selected Stocks:\n" + "\n".join([
        f"{row['Name']} - Score: {row['Total Score']:.2f}"
        for index, row in df.iterrows()
    ])
    payload = {
        "text": message
    }
    response = requests.post(webhook_url, json=payload)
    print("Notification sent:", response.status_code)
EOF

cat > turing_filter_for_a_stock/tests/test_main.py << EOF
import unittest
import main

class TestMain(unittest.TestCase):
    def test_main(self):
        # Test main functionality
        pass

if __name__ == '__main__':
    unittest.main()
EOF