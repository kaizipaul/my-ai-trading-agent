"""
Tests for the FOREX.com API client implementation
"""
import unittest
import os
import sys
from datetime import datetime

# Add project root to Python path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from src.utils.forex_dot_com_client import ForexDotComClient
from src.utils.forex_data_fetcher import ForexDataFetcher
from src.utils.order_executor import OrderExecutor

class TestForexDotComClient(unittest.TestCase):
    """Tests for the FOREX.com API client implementation"""
    
    def setUp(self):
        """Set up the test environment"""
        # Force development mode to avoid actual API calls
        os.environ["ENVIRONMENT"] = "development"
        
        # Initialize the client
        self.client = ForexDotComClient()
        self.data_fetcher = ForexDataFetcher()
        self.order_executor = OrderExecutor()
        
    def test_client_initialization(self):
        """Test that the client initializes correctly"""
        self.assertIsNotNone(self.client)
        # The client should read ENVIRONMENT from os.getenv with a default
        self.assertEqual(self.client.environment, os.getenv("ENVIRONMENT", "development"))
        
    def test_symbol_formatting(self):
        """Test that symbols are formatted correctly"""
        self.assertEqual(self.client.format_symbol("EUR/USD"), "EUR_USD")
        self.assertEqual(self.client.format_symbol("GBP/JPY"), "GBP_JPY")
        self.assertEqual(self.client.format_symbol("XAU/USD"), "XAU_USD")
        
    def test_simulated_data_fetching(self):
        """Test that simulated data fetching works correctly"""
        # Get price data
        df = self.data_fetcher.get_price_data("EUR/USD", "H1", 50)
        
        # Verify the data
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 50)  # Should have 50 candles
        self.assertTrue("open" in df.columns)
        self.assertTrue("high" in df.columns)
        self.assertTrue("low" in df.columns)
        self.assertTrue("close" in df.columns)
        self.assertTrue("volume" in df.columns)
        
    def test_simulated_current_price(self):
        """Test that simulated current price fetching works correctly"""
        # Get current price
        price = self.data_fetcher.get_current_price("EUR/USD")
        
        # Verify the price
        self.assertIsNotNone(price)
        self.assertIsInstance(price, float)
        self.assertGreater(price, 0)
        
    def test_simulated_order_execution(self):
        """Test that simulated order execution works correctly"""
        # Place a market order
        order = self.order_executor.place_market_order(
            pair="EUR/USD",
            direction="buy",
            units=1000,
            stop_loss=1.1000,
            take_profit=1.1500
        )
        
        # Verify the order
        self.assertIsNotNone(order)
        self.assertEqual(order["pair"], "EUR/USD")
        self.assertEqual(order["direction"], "buy")
        self.assertEqual(order["units"], 1000)
        self.assertEqual(order["stop_loss"], 1.1000)
        self.assertEqual(order["take_profit"], 1.1500)
        
        # Verify the order has an ID and status
        self.assertIn("orderId", order)
        self.assertIn("status", order)
        self.assertIn("sim-", order["orderId"])  # Order ID should contain "sim-" prefix
        self.assertEqual(order["status"], "FILLED")
        
if __name__ == "__main__":
    unittest.main() 