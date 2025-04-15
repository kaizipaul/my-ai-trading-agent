"""
News sentiment analysis agent for forex trading
"""
import os
from newsapi import NewsApiClient
from datetime import datetime, timedelta
from termcolor import cprint
from transformers import pipeline
import pandas as pd
from src.config import FOREX_PAIRS

class NewsSentimentAgent:
    def __init__(self):
        self.newsapi = NewsApiClient(api_key=os.getenv('NEWS_API_KEY'))
        # Load sentiment analyzer
        self.sentiment_analyzer = pipeline('sentiment-analysis', 
                                         model='finiteautomata/bertweet-base-sentiment-analysis')
        self.sentiment_scores = {}
        
    def run(self):
        """Main news sentiment analysis cycle"""
        try:
            for pair in FOREX_PAIRS:
                sentiment = self.analyze_pair_sentiment(pair)
                self.sentiment_scores[pair] = sentiment
                self.announce_significant_sentiment(pair, sentiment)
                
        except Exception as e:
            cprint(f"❌ Error in news sentiment analysis: {str(e)}", "red")
            
    def analyze_pair_sentiment(self, pair):
        """Analyze news sentiment for a specific pair"""
        try:
            # Convert pair to search terms (e.g., 'EUR/USD' -> ['Euro', 'Dollar'])
            search_terms = self.get_search_terms(pair)
            
            # Get news articles
            articles = []
            for term in search_terms:
                news = self.newsapi.get_everything(
                    q=term,
                    language='en',
                    sort_by='relevancy',
                    from_param=(datetime.now() - timedelta(days=1)).date().isoformat(),
                    to=datetime.now().date().isoformat()
                )
                articles.extend(news['articles'])
                
            if not articles:
                return {'score': 0, 'magnitude': 0, 'articles_analyzed': 0}
                
            # Analyze sentiment
            sentiments = []
            for article in articles:
                text = f"{article['title']} {article['description']}" if article['description'] else article['title']
                sentiment = self.sentiment_analyzer(text)[0]
                sentiments.append(sentiment)
                
            # Calculate aggregate sentiment
            sentiment_scores = [1 if s['label'] == 'POS' else -1 if s['label'] == 'NEG' else 0 for s in sentiments]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            magnitude = abs(avg_sentiment)
            
            return {
                'score': avg_sentiment,
                'magnitude': magnitude,
                'articles_analyzed': len(articles)
            }
            
        except Exception as e:
            cprint(f"❌ Error analyzing sentiment for {pair}: {str(e)}", "red")
            return {'score': 0, 'magnitude': 0, 'articles_analyzed': 0}
            
    def get_search_terms(self, pair):
        """Convert forex pair to search terms"""
        currency_terms = {
            'EUR': ['Euro', 'ECB', 'European Central Bank'],
            'USD': ['Dollar', 'Fed', 'Federal Reserve'],
            'GBP': ['Pound Sterling', 'Bank of England'],
            'JPY': ['Yen', 'Bank of Japan'],
            'XAU': ['Gold', 'Gold price', 'Precious metals']
        }
        
        base, quote = pair.split('/')
        return currency_terms.get(base, [base]) + currency_terms.get(quote, [quote])
        
    def announce_significant_sentiment(self, pair, sentiment):
        """Announce significant sentiment changes"""
        if abs(sentiment['score']) > 0.5:  # Significant sentiment threshold
            direction = "positive" if sentiment['score'] > 0 else "negative"
            cprint(f"📰 Strong {direction} sentiment detected for {pair}", "yellow")
            cprint(f"   Score: {sentiment['score']:.2f}", "cyan")
            cprint(f"   Based on {sentiment['articles_analyzed']} articles", "cyan")
