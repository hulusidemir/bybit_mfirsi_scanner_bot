import ccxt
import pandas as pd
import pandas_ta as ta
import time
from src.config import (
    BYBIT_API_KEY, BYBIT_API_SECRET, TIMEFRAME,
    RSI_PERIOD, MFI_PERIOD, RSI_OVERSOLD, MFI_OVERSOLD,
    RSI_OVERBOUGHT, MFI_OVERBOUGHT, MIN_24H_VOLUME_USDT
)

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
                data['next_funding'] = funding_info.get('fundingTimestamp', 'N/A')
            except Exception as e:
                print(f"Error fetching funding rate for {symbol}: {e}")

            # Open Interest
            try:
                oi_data = self.exchange.fetch_open_interest(symbol)
                data['open_interest'] = oi_data.get('openInterestAmount', 'N/A')
            except Exception as e:
                print(f"Error fetching open interest for {symbol}: {e}")

            # 24h Stats for Volume
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                data['volume_24h'] = ticker.get('quoteVolume', 'N/A')
            except Exception as e:
                print(f"Error fetching ticker for {symbol}: {e}")

            return data
        except Exception as e:
            print(f"Error in get_market_data for {symbol}: {e}")
            return data

    def analyze_coin(self, symbol):
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
            market_data = self.get_market_data(symbol)
            if market_data:
                return {
                    'symbol': symbol,
                    'signal': signal,
                    'rsi': rsi,
                    'mfi': mfi,
                    'price': last_candle['close'],
                    'vwap': last_candle['VWAP'],
                    **market_data
                }
        
        return None
