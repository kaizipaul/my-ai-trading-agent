"""
Basic tests for the trading system
"""
import sys
import os
import unittest
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Import from src
from src.strategies.moving_average_strategy import MovingAverageStrategy
from src.utils.technical_analysis import TechnicalAnalysis
from src.utils.position_manager import PositionManager
from src.utils.order_executor import OrderExecutor
import pandas as pd
import numpy as np

class TestTradingSystem(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Create some test data
        dates = pd.date_range(start='2023-01-01', periods=300, freq='1h')
        self.test_data = pd.DataFrame({
            'open': np.random.normal(1.1, 0.02, 300),
            'high': np.random.normal(1.11, 0.02, 300),
            'low': np.random.normal(1.09, 0.02, 300),
            'close': np.random.normal(1.1, 0.02, 300),
            'volume': np.random.randint(100, 10000, 300)
        }, index=dates)
        
        # Add technical indicators
        self.test_data = TechnicalAnalysis.add_all_indicators(self.test_data)
        
        # Initialize test instances
        self.strategy = MovingAverageStrategy()
        self.position_manager = PositionManager(data_dir='tests/data')
        self.order_executor = OrderExecutor()
        
    def test_moving_average_strategy(self):
        """Test the moving average strategy"""
        signal = self.strategy.generate_signal('EUR/USD', self.test_data)
        
        # The signal might be None depending on the random data
        if signal is not None:
            self.assertIn('should_trade', signal)
            self.assertIn('direction', signal)
            self.assertIn('confidence', signal)
            self.assertIn('entry_price', signal)
            self.assertIn('stop_loss', signal)
            self.assertIn('take_profit', signal)
        
    def test_position_manager(self):
        """Test the position manager"""
        # Test position creation
        position = self.position_manager.open_position(
            'EUR/USD', 'buy', 1.1000, 1000, 1.0950, 1.1100
        )
        self.assertEqual(position['pair'], 'EUR/USD')
        self.assertEqual(position['direction'], 'buy')
        
        # Test position update
        updated = self.position_manager.update_position('EUR/USD', 1.1050)
        self.assertGreater(updated['unrealized_pl'], 0)
        
        # Test position close
        closed = self.position_manager.close_position('EUR/USD', 1.1020)
        self.assertEqual(closed['pair'], 'EUR/USD')
        self.assertNotIn('EUR/USD', self.position_manager.positions)
        
    def test_position_size_calculation(self):
        """Test position size calculation"""
        size = self.position_manager.calculate_position_size('EUR/USD', 1.1000, 1.0950)
        self.assertGreater(size, 0)
        
    def tearDown(self):
        """Clean up after tests"""
        # Remove test data files
        test_files = [
            'tests/data/positions.json',
            'tests/data/trade_history.json'
        ]
        for file in test_files:
            if os.path.exists(file):
                os.remove(file)
        
        if os.path.exists('tests/data'):
            os.rmdir('tests/data')
            
if __name__ == '__main__':
    unittest.main() 