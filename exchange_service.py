import requests
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from models import OpenInterestData, ExchangeOpenInterestData
from config import BINANCE_API_KEY, BINANCE_API_SECRET, BYBIT_API_KEY, BYBIT_API_SECRET

class BinanceOpenInterestService:
    """Service to fetch open interest data from Binance"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, token_list: Optional[list] = None):
        self.api_key = api_key or BINANCE_API_KEY
        self.api_secret = api_secret or BINANCE_API_SECRET
        self.base_url = "https://fapi.binance.com"
        self.token_list = token_list
    
    def get_open_interest_data(self) -> ExchangeOpenInterestData:
        """Fetch open interest data from Binance"""
        try:
            open_interest_data = []
            
            # Get top symbols for monitoring (simplified approach)
            symbols = self.token_list if self.token_list else ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT", 
                      "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "MATICUSDT", "LINKUSDT"]
            
            for symbol in symbols:
                try:
                    # Get open interest
                    oi_url = f"{self.base_url}/fapi/v1/openInterest"
                    oi_params = {"symbol": symbol}
                    oi_response = requests.get(oi_url, params=oi_params, timeout=10)
                    
                    if oi_response.status_code == 200:
                        oi_data = oi_response.json()
                        
                        # Get ticker for price
                        ticker_url = f"{self.base_url}/fapi/v1/ticker/24hr"
                        ticker_params = {"symbol": symbol}
                        ticker_response = requests.get(ticker_url, params=ticker_params, timeout=10)
                        
                        price = 0.0
                        volume = 0.0
                        if ticker_response.status_code == 200:
                            ticker_data = ticker_response.json()
                            price = float(ticker_data.get('lastPrice', 0))
                            volume = float(ticker_data.get('quoteVolume', 0))
                        
                        # Get funding rate
                        funding_url = f"{self.base_url}/fapi/v1/fundingRate"
                        funding_params = {"symbol": symbol, "limit": 1}
                        funding_response = requests.get(funding_url, params=funding_params, timeout=10)
                        
                        funding_rate = None
                        if funding_response.status_code == 200:
                            funding_data = funding_response.json()
                            if funding_data:
                                funding_rate = float(funding_data[0].get('fundingRate', 0))
                        
                        oi_value = float(oi_data.get('openInterest', 0)) * price
                        
                        oi_record = OpenInterestData(
                            symbol=symbol,
                            exchange='binance',
                            open_interest=float(oi_data.get('openInterest', 0)),
                            open_interest_value=oi_value,
                            timestamp=datetime.now(),
                            price=price,
                            volume_24h=volume,
                            funding_rate=funding_rate
                        )
                        
                        open_interest_data.append(oi_record)
                    
                except Exception as e:
                    logging.warning(f"Error fetching data for {symbol}: {e}")
                    continue
            
            return ExchangeOpenInterestData(
                exchange='binance',
                data=open_interest_data,
                timestamp=datetime.now(),
                success=True
            )
            
        except Exception as e:
            logging.error(f"Error fetching Binance open interest data: {e}")
            return ExchangeOpenInterestData(
                exchange='binance',
                data=[],
                timestamp=datetime.now(),
                success=False,
                error=str(e)
            )

class BybitOpenInterestService:
    """Service to fetch open interest data from Bybit"""
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None, token_list: Optional[list] = None):
        self.api_key = api_key or BYBIT_API_KEY
        self.api_secret = api_secret or BYBIT_API_SECRET
        self.base_url = "https://api.bybit.com"
        self.token_list = token_list
    
    def get_open_interest_data(self) -> ExchangeOpenInterestData:
        """Fetch open interest data from Bybit"""
        try:
            open_interest_data = []
            
            # Get top symbols for monitoring
            symbols = self.token_list if self.token_list else ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "SOLUSDT", 
                      "DOTUSDT", "DOGEUSDT", "AVAXUSDT", "MATICUSDT", "LINKUSDT"]
            
            for symbol in symbols:
                try:
                    # Get open interest
                    oi_url = f"{self.base_url}/v5/market/open-interest"
                    oi_params = {"category": "linear", "symbol": symbol}
                    oi_response = requests.get(oi_url, params=oi_params, timeout=10)
                    
                    if oi_response.status_code == 200:
                        oi_data = oi_response.json()
                        
                        if oi_data.get('retCode') == 0 and oi_data.get('result', {}).get('list'):
                            oi_info = oi_data['result']['list'][0]
                            
                            # Get ticker for price
                            ticker_url = f"{self.base_url}/v5/market/tickers"
                            ticker_params = {"category": "linear", "symbol": symbol}
                            ticker_response = requests.get(ticker_url, params=ticker_params, timeout=10)
                            
                            price = 0.0
                            volume = 0.0
                            if ticker_response.status_code == 200:
                                ticker_data = ticker_response.json()
                                if ticker_data.get('retCode') == 0 and ticker_data.get('result', {}).get('list'):
                                    ticker_info = ticker_data['result']['list'][0]
                                    price = float(ticker_info.get('lastPrice', 0))
                                    volume = float(ticker_info.get('turnover24h', 0))
                            
                            # Get funding rate
                            funding_url = f"{self.base_url}/v5/market/funding/history"
                            funding_params = {"category": "linear", "symbol": symbol, "limit": 1}
                            funding_response = requests.get(funding_url, params=funding_params, timeout=10)
                            
                            funding_rate = None
                            if funding_response.status_code == 200:
                                funding_data = funding_response.json()
                                if funding_data.get('retCode') == 0 and funding_data.get('result', {}).get('list'):
                                    funding_info = funding_data['result']['list'][0]
                                    funding_rate = float(funding_info.get('fundingRate', 0))
                            
                            oi_record = OpenInterestData(
                                symbol=symbol,
                                exchange='bybit',
                                open_interest=float(oi_info.get('openInterest', 0)),
                                open_interest_value=float(oi_info.get('openInterestValue', 0)),
                                timestamp=datetime.now(),
                                price=price,
                                volume_24h=volume,
                                funding_rate=funding_rate
                            )
                            
                            open_interest_data.append(oi_record)
                    
                except Exception as e:
                    logging.warning(f"Error fetching data for {symbol}: {e}")
                    continue
            
            return ExchangeOpenInterestData(
                exchange='bybit',
                data=open_interest_data,
                timestamp=datetime.now(),
                success=True
            )
            
        except Exception as e:
            logging.error(f"Error fetching Bybit open interest data: {e}")
            return ExchangeOpenInterestData(
                exchange='bybit',
                data=[],
                timestamp=datetime.now(),
                success=False,
                error=str(e)
            )

class OpenInterestAggregator:
    """Aggregator to fetch open interest data from multiple exchanges"""
    
    def __init__(self, token_list: Optional[list] = None):
        self.binance_service = BinanceOpenInterestService(token_list=token_list)
        self.bybit_service = BybitOpenInterestService(token_list=token_list)
    
    def get_all_exchange_data(self) -> Dict[str, ExchangeOpenInterestData]:
        """Fetch open interest data from all supported exchanges"""
        results = {}
        
        # Fetch from Binance
        try:
            binance_data = self.binance_service.get_open_interest_data()
            results['binance'] = binance_data
        except Exception as e:
            logging.error(f"Error fetching Binance data: {e}")
            results['binance'] = ExchangeOpenInterestData(
                exchange='binance',
                data=[],
                timestamp=datetime.now(),
                success=False,
                error=str(e)
            )
        
        # Fetch from Bybit
        try:
            bybit_data = self.bybit_service.get_open_interest_data()
            results['bybit'] = bybit_data
        except Exception as e:
            logging.error(f"Error fetching Bybit data: {e}")
            results['bybit'] = ExchangeOpenInterestData(
                exchange='bybit',
                data=[],
                timestamp=datetime.now(),
                success=False,
                error=str(e)
            )
        
        return results 