import ccxt
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime, timedelta
from src.config import (
    BYBIT_API_KEY, BYBIT_API_SECRET, TIMEFRAME,
    RSI_PERIOD, MFI_PERIOD, RSI_OVERSOLD, MFI_OVERSOLD,
    RSI_OVERBOUGHT, MFI_OVERBOUGHT, MIN_24H_VOLUME_USDT
)
from src.coingecko_manager import CoinGeckoManager

class Scanner:
    def __init__(self):
        self.exchange = ccxt.bybit({
            'apiKey': BYBIT_API_KEY,
            'secret': BYBIT_API_SECRET,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',  # Use 'swap' for perpetual futures
            }
        })
        self.cg_manager = CoinGeckoManager()

    def get_tickers(self):
        """Fetch all USDT tickers and filter by volume"""
        try:
            tickers = self.exchange.fetch_tickers()
            filtered_symbols = []
            for symbol, data in tickers.items():
                # Filter for USDT pairs and Volume
                if '/USDT' in symbol and data['quoteVolume'] is not None:
                    if data['quoteVolume'] >= MIN_24H_VOLUME_USDT:
                        filtered_symbols.append(symbol)
            print(f"Found {len(filtered_symbols)} pairs matching criteria.")
            return filtered_symbols
        except Exception as e:
            print(f"Error fetching tickers: {e}")
            return []

    def fetch_ohlcv(self, symbol, limit=100):
        """Fetch OHLCV data"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=limit)
            if not ohlcv:
                return None
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            print(f"Error fetching OHLCV for {symbol}: {e}")
            return None

    def calculate_indicators(self, df):
        """Calculate RSI, MFI, and VWAP"""
        try:
            # RSI
            df['RSI'] = ta.rsi(df['close'], length=RSI_PERIOD)
            
            # MFI
            df['MFI'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=MFI_PERIOD)
            
            # VWAP
            df['VWAP'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])
            
            return df
        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return df

    def get_market_data(self, symbol):
        """Fetch additional market data like Funding Rate and Open Interest"""
        data = {
            'funding_rate': 'N/A',
            'next_funding': 'N/A',
            'open_interest': 'N/A',
            'volume_24h': 'N/A',
            'ls_ratio': 'N/A'
        }
        
        try:
            # Funding Rate
            try:
                funding_info = self.exchange.fetch_funding_rate(symbol)
                data['funding_rate'] = funding_info.get('fundingRate', 'N/A')
                
                next_funding_ts = funding_info.get('fundingTimestamp')
                if next_funding_ts:
                    now = time.time() * 1000
                    diff = next_funding_ts - now
                    if diff > 0:
                        td = timedelta(milliseconds=diff)
                        # Format as HH:MM:SS
                        data['next_funding'] = str(td).split('.')[0]
                    else:
                        data['next_funding'] = "00:00:00"
            except Exception as e:
                print(f"Error fetching funding rate for {symbol}: {e}")

            # Open Interest
            try:
                oi_data = self.exchange.fetch_open_interest(symbol)
                oi_val = oi_data.get('openInterestAmount')
                if oi_val:
                    data['open_interest'] = f"{oi_val:,.0f}"
            except Exception as e:
                print(f"Error fetching open interest for {symbol}: {e}")

            # 24h Stats for Volume
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                data['volume_24h'] = ticker.get('quoteVolume', 'N/A')
            except Exception as e:
                print(f"Error fetching ticker for {symbol}: {e}")

            # Long/Short Ratio
            try:
                # Bybit V5 API for Long/Short Ratio
                # period: 5min, 15min, 30min, 1h, 4h, 1d
                # We use the same timeframe as the bot or '15min' explicitly
                market_symbol = symbol.replace('/', '')
                response = self.exchange.request(
                    path='v5/market/account-ratio',
                    api='public',
                    method='GET',
                    params={
                        'category': 'linear',
                        'symbol': market_symbol,
                        'period': '15min',
                        'limit': 1
                    }
                )
                if response and 'result' in response and 'list' in response['result']:
                    items = response['result']['list']
                    if items:
                        ratio = items[0].get('ratio', 'N/A')
                        data['ls_ratio'] = ratio
            except Exception as e:
                # Silent fail or debug print
                # print(f"Error fetching L/S ratio for {symbol}: {e}")
                pass

            return data
        except Exception as e:
            print(f"Error in get_market_data for {symbol}: {e}")
            return data

    def analyze_coin(self, symbol):
        print(f"Analyzing {symbol}...", end='\r')
        df = self.fetch_ohlcv(symbol)
        if df is None or len(df) < RSI_PERIOD:
            return None

        df = self.calculate_indicators(df)
        
        # Get latest completed candle (iloc[-2] usually, as -1 is current forming candle)
        # However, for signals, sometimes we want the current forming candle or the last closed one.
        # Let's use the last closed candle to avoid repainting.
        last_candle = df.iloc[-2]
        current_candle = df.iloc[-1] # Just for reference if needed

        rsi = last_candle['RSI']
        mfi = last_candle['MFI']
        
        signal = None
        
        # Strategy Logic
        # Long: RSI < 20 and MFI < 25
        if rsi < RSI_OVERSOLD and mfi < MFI_OVERSOLD:
            signal = 'LONG'
            
        # Short: RSI > 80 and MFI > 80
        elif rsi > RSI_OVERBOUGHT and mfi > MFI_OVERBOUGHT:
            signal = 'SHORT'
            
        if signal:
            print(f"\nSignal found for {symbol}: {signal}")
            market_data = self.get_market_data(symbol)
            cg_data = self.cg_manager.get_coin_details(symbol)
            
            if market_data:
                result = {
                    'symbol': symbol,
                    'signal': signal,
                    'rsi': rsi,
                    'mfi': mfi,
                    'price': last_candle['close'],
                    'vwap': last_candle['VWAP'],
                    **market_data
                }
                if cg_data:
                    result.update(cg_data)
                return result
        
        return None
