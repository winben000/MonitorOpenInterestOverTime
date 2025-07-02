from dataclasses import dataclass
from typing import Optional, Dict, List
from datetime import datetime
import json

@dataclass
class OpenInterestData:
    """Data structure for open interest information"""
    symbol: str
    exchange: str
    open_interest: float
    open_interest_value: float  # in USD
    timestamp: datetime
    price: Optional[float] = None
    volume_24h: Optional[float] = None
    funding_rate: Optional[float] = None

@dataclass
class OpenInterestAlert:
    """Data structure for open interest alerts"""
    symbol: str
    exchange: str
    current_oi: float
    previous_oi: float
    percentage_change: float
    timestamp: datetime
    alert_type: str  # "spike" or "drop"
    severity: str  # "high", "medium", "low"

@dataclass
class ExchangeOpenInterestData:
    """Data structure for exchange open interest results"""
    exchange: str
    data: List[OpenInterestData]
    timestamp: datetime
    success: bool
    error: Optional[str] = None

class OpenInterestDataEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj) 