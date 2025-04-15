"""
Base strategy template for financial market analysis
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

class BaseStrategy(ABC):
    """
    Base class for all trading strategies.
    Provides standardized interfaces for analysis, signal generation, and recommendation output.
    """
    
    def __init__(self, name: str, params: Dict = None):
        self.name = name
        self.params = params or {}
        self.signals = []
        self.analysis_results = {}
        
    @abstractmethod
    def analyze(self, data: pd.DataFrame) -> Dict:
        """
        Analyze market data and generate insights.
        
        Args:
            data: DataFrame containing price and volume data
            
        Returns:
            Dictionary containing analysis results
        """
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[Dict]:
        """
        Generate trading signals based on analysis.
        
        Args:
            data: DataFrame containing price and volume data
            
        Returns:
            List of signal dictionaries with timestamp, type, and confidence
        """
        pass
    
    @abstractmethod
    def get_recommendation(self, data: pd.DataFrame) -> Dict:
        """
        Generate a trading recommendation based on current market conditions.
        
        Args:
            data: DataFrame containing price and volume data
            
        Returns:
            Dictionary containing recommendation details
        """
        pass
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """
        Validate input data has required columns and format.
        
        Args:
            data: DataFrame to validate
            
        Returns:
            bool: True if data is valid, False otherwise
        """
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        return all(col in data.columns for col in required_columns)
    
    def calculate_returns(self, data: pd.DataFrame) -> pd.Series:
        """
        Calculate returns for the given data.
        
        Args:
            data: DataFrame containing price data
            
        Returns:
            Series of returns
        """
        return data['close'].pct_change()
    
    def get_strategy_info(self) -> Dict:
        """
        Get information about the strategy.
        
        Returns:
            Dictionary containing strategy metadata
        """
        return {
            'name': self.name,
            'parameters': self.params,
            'description': self.__doc__
        }