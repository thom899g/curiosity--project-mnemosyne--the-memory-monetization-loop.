"""
Firebase initialization with connection pooling and automatic reconnection.
Architectural Choice: Uses Firestore for state persistence and Realtime Database 
for streaming trading signals to minimize memory footprint.
"""
import os
import logging
from typing import Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import firebase_admin
from firebase_admin import credentials, firestore, db
from firebase_admin.exceptions import FirebaseError

logger = logging.getLogger(__name__)

@dataclass
class TradingState:
    """Immutable state container to prevent memory fragmentation"""
    last_arbitrage_ts: datetime
    cumulative_profit_usdc: float
    active_positions: int
    memory_usage_mb: float
    
class FirebaseManager:
    """Singleton manager for Firebase connections with connection pooling"""
    
    _instance: Optional['FirebaseManager'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.app = None
            self.firestore_client: Optional[firestore.Client] = None
            self.rtdb = None
            self._init_firebase()
            self._initialized = True
    
    def _init_firebase(self) -> None:
        """Initialize Firebase with exponential backoff retry logic"""
        try:
            cred