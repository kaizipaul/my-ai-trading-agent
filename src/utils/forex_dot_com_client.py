"""
FOREX.com API client implementation
"""
import os
import requests
import json
import time
from datetime import datetime
from termcolor import cprint
from dotenv import load_dotenv

# Load environment variables if not already loaded
load_dotenv()

class ForexDotComClient:
    """
    Client for interacting with FOREX.com's REST API
    
    This is a generic implementation that will need to be updated
    based on FOREX.com's specific API documentation.
    """
    
    def __init__(self):
        """Initialize the FOREX.com API client"""
        self.api_key = os.getenv("FOREXCOM_API_KEY")
        self.api_secret = os.getenv("FOREXCOM_API_SECRET")
        self.account_id = os.getenv("FOREXCOM_ACCOUNT_ID")
        self.environment = os.getenv("ENVIRONMENT", "development")
        
        # Base API URLs - update these with actual FOREX.com endpoints
        self.base_url = os.getenv("FOREXCOM_API_URL", "https://api.forex.com/api/v1")
        self.streaming_url = os.getenv("FOREXCOM_STREAMING_URL", "wss://streaming.forex.com/v1")
        
        # Default headers for API requests
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "X-API-KEY": self.api_key
        }
        
        # Optional: Verify connection on init
        if self.environment != "development":
            self._verify_connection()
    
    def _verify_connection(self):
        """Verify connection to the API"""
        try:
            response = self.get_account_info()
            if response:
                cprint(f"✅ Connected to FOREX.com API", "green")
                return True
            return False
        except Exception as e:
            cprint(f"❌ Error connecting to FOREX.com API: {str(e)}", "red")
            return False
    
    def _make_request(self, method, endpoint, params=None, data=None):
        """Make a request to the FOREX.com API"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=self.headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=self.headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse JSON response
            return response.json()
        
        except requests.exceptions.RequestException as e:
            cprint(f"❌ API request error: {str(e)}", "red")
            if hasattr(e, 'response') and e.response:
                try:
                    error_data = e.response.json()
                    cprint(f"API Error: {json.dumps(error_data, indent=2)}", "red")
                except:
                    cprint(f"Status Code: {e.response.status_code}", "red")
                    cprint(f"Response: {e.response.text}", "red")
            return None
    
    # Account endpoints
    def get_account_info(self):
        """Get account information"""
        return self._make_request("GET", f"accounts/{self.account_id}")
    
    # Market data endpoints
    def get_price_data(self, symbol, timeframe, count=100):
        """Get historical price data for a symbol"""
        params = {
            "count": count,
            "granularity": timeframe
        }
        return self._make_request("GET", f"instruments/{symbol}/candles", params=params)
    
    def get_current_price(self, symbol):
        """Get current price for a symbol"""
        params = {
            "count": 1,
            "granularity": "S5"  # 5-second candles
        }
        response = self._make_request("GET", f"instruments/{symbol}/candles", params=params)
        if response and 'candles' in response and len(response['candles']) > 0:
            return response['candles'][0]['mid']['c']
        return None
    
    # Trading endpoints
    def place_market_order(self, symbol, direction, units, stop_loss=None, take_profit=None):
        """Place a market order"""
        data = {
            "order": {
                "type": "MARKET",
                "instrument": symbol,
                "units": str(units) if direction.lower() == "buy" else str(-units),
                "timeInForce": "FOK",
                "positionFill": "DEFAULT"
            }
        }
        
        # Add stop loss if provided
        if stop_loss is not None:
            data["order"]["stopLossOnFill"] = {
                "price": str(stop_loss),
                "timeInForce": "GTC"
            }
            
        # Add take profit if provided
        if take_profit is not None:
            data["order"]["takeProfitOnFill"] = {
                "price": str(take_profit),
                "timeInForce": "GTC"
            }
        
        return self._make_request("POST", f"accounts/{self.account_id}/orders", data=data)
    
    def close_trade(self, trade_id):
        """Close a specific trade"""
        return self._make_request("PUT", f"accounts/{self.account_id}/trades/{trade_id}/close")
    
    def close_all_positions(self):
        """Close all open positions"""
        return self._make_request("PUT", f"accounts/{self.account_id}/positions/close")
    
    def modify_trade(self, trade_id, stop_loss=None, take_profit=None):
        """Modify an existing trade"""
        data = {}
        if stop_loss is not None:
            data["stopLoss"] = {
                "price": str(stop_loss),
                "timeInForce": "GTC"
            }
        if take_profit is not None:
            data["takeProfit"] = {
                "price": str(take_profit),
                "timeInForce": "GTC"
            }
        
        return self._make_request("PUT", f"accounts/{self.account_id}/trades/{trade_id}/orders", data=data)
    
    # Helper methods
    def format_symbol(self, pair):
        """Format a currency pair for FOREX.com (e.g., 'EUR/USD' to 'EUR_USD')"""
        return pair.replace('/', '_') 