import ccxt
import pandas as pd
import pandas_ta as ta
import time
from datetime import datetime, timedelta
from src.config import (
    BYBIT_API_KEY, BYBIT_API_SECRET, TIMEFRAME,
    RSI_PERIOD, MFI_PERIOD, RSI_OVERSOLD, MFI_OVERSOLD,
    RSI_OVERBOUGHT, MFI_OVERBOUGHT, MIN_24H_VOLUME_USDT,
    PSAR_ENABLED, PSAR_AF, PSAR_MAX, PSAR_CONSECUTIVE_BARS,
    TD_SEQ_ENABLED
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

    def calculate_td_sequential(self, df):
        """Calculate TD Sequential Setup"""
        try:
            close = df['close']
            
            td_buy = []
            td_sell = []
            
            buy_count = 0
            sell_count = 0
            
            for i in range(len(df)):
                if i < 4:
                    td_buy.append(0)
                    td_sell.append(0)
                    continue
                    
                c = close.iloc[i]
                c4 = close.iloc[i-4]
                
                # Buy Setup: Close < Close[4]
                if c < c4:
                    buy_count += 1
                else:
                    buy_count = 0
                    
                # Sell Setup: Close > Close[4]
                if c > c4:
                    sell_count += 1
                else:
                    sell_count = 0
                    
                td_buy.append(buy_count)
                td_sell.append(sell_count)
                
            df['TD_Buy'] = td_buy
            df['TD_Sell'] = td_sell
            return df
        except Exception as e:
            print(f"Error calculating TD Sequential: {e}")
            return df

    def calculate_indicators(self, df):
        """Calculate RSI, MFI, VWAP, and ADX"""
        try:
            # RSI
            df['RSI'] = ta.rsi(df['close'], length=RSI_PERIOD)
            
            # MFI
            df['MFI'] = ta.mfi(df['high'], df['low'], df['close'], df['volume'], length=MFI_PERIOD)
            
            # VWAP
            df['VWAP'] = ta.vwap(df['high'], df['low'], df['close'], df['volume'])

            # ADX
            adx = ta.adx(df['high'], df['low'], df['close'], length=14)
            if adx is not None:
                df = pd.concat([df, adx], axis=1)

            # Parabolic SAR
            if PSAR_ENABLED:
                psar = ta.psar(df['high'], df['low'], df['close'], af0=PSAR_AF, af=PSAR_AF, max_af=PSAR_MAX)
                if psar is not None:
                    # Combine PSARl and PSARs into one column
                    # Column names are dynamic based on AF and MAX
                    psar_l_col = f"PSARl_{PSAR_AF}_{PSAR_MAX}"
                    psar_s_col = f"PSARs_{PSAR_AF}_{PSAR_MAX}"
                    
                    # Check if columns exist (pandas_ta might format float differently in string)
                    # A safer way is to take the first two columns which are usually Long and Short
                    if not psar.empty:
                        df['PSAR'] = psar.iloc[:, 0].fillna(psar.iloc[:, 1])

            # TD Sequential
            if TD_SEQ_ENABLED:
                df = self.calculate_td_sequential(df)
            
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
                market = self.exchange.market(symbol)
                market_id = market['id']
                
                response = self.exchange.request(
                    path='v5/market/account-ratio',
                    api='public',
                    method='GET',
                    params={
                        'category': 'linear',
                        'symbol': market_id,
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
        adx = last_candle.get('ADX_14', 0)
        
        signal = None
        td_note = ""
        
        # Strategy Logic
        # Long: RSI < 20 and MFI < 25
        if rsi < RSI_OVERSOLD and mfi < MFI_OVERSOLD:
            signal = 'LONG'
            if PSAR_ENABLED and 'PSAR' in df.columns:
                # Check if price has been BELOW PSAR for the last N bars
                # We look at the last N closed candles
                last_n_candles = df.iloc[-(PSAR_CONSECUTIVE_BARS + 1):-1]
                if len(last_n_candles) < PSAR_CONSECUTIVE_BARS:
                    signal = None # Not enough data
                else:
                    # Check if ALL closes are < PSAR
                    if not (last_n_candles['close'] < last_n_candles['PSAR']).all():
                        signal = None
            
            if TD_SEQ_ENABLED and signal == 'LONG':
                # Check last 5 closed candles for TD Buy 9 or 13
                # df.iloc[-2] is last_candle (closed)
                # We want range [-6:-1] -> indices -6, -5, -4, -3, -2
                recent_td = df['TD_Buy'].iloc[-6:-1]
                has_9 = (recent_td == 9).any()
                has_13 = (recent_td == 13).any()
                
                if not (has_9 or has_13):
                    signal = None
                else:
                    if has_13:
                        td_note = "TD Buy 13"
                    else:
                        td_note = "TD Buy 9"

        # Short: RSI > 80 and MFI > 80
        elif rsi > RSI_OVERBOUGHT and mfi > MFI_OVERBOUGHT:
            signal = 'SHORT'
            if PSAR_ENABLED and 'PSAR' in df.columns:
                # Check if price has been ABOVE PSAR for the last N bars
                last_n_candles = df.iloc[-(PSAR_CONSECUTIVE_BARS + 1):-1]
                if len(last_n_candles) < PSAR_CONSECUTIVE_BARS:
                    signal = None
                else:
                    # Check if ALL closes are > PSAR
                    if not (last_n_candles['close'] > last_n_candles['PSAR']).all():
                        signal = None
            
            if TD_SEQ_ENABLED and signal == 'SHORT':
                # Check last 5 closed candles for TD Sell 9 or 13
                recent_td = df['TD_Sell'].iloc[-6:-1]
                has_9 = (recent_td == 9).any()
                has_13 = (recent_td == 13).any()
                
                if not (has_9 or has_13):
                    signal = None
                else:
                    if has_13:
                        td_note = "TD Sell 13"
                    else:
                        td_note = "TD Sell 9"
            
        if signal:
            print(f"\nSignal found for {symbol}: {signal} {td_note}")
            market_data = self.get_market_data(symbol)
            cg_data = self.cg_manager.get_coin_details(symbol)
            
            if market_data:
                result = {
                    'symbol': symbol,
                    'signal': signal,
                    'rsi': rsi,
                    'mfi': mfi,
                    'adx': adx,
                    'price': last_candle['close'],
                    'vwap': last_candle['VWAP'],
                    'psar': last_candle['PSAR'] if 'PSAR' in last_candle else 'N/A',
                    'td_buy': last_candle.get('TD_Buy', 0),
                    'td_sell': last_candle.get('TD_Sell', 0),
                    'td_note': td_note,
                    **market_data
                }
                if cg_data:
                    result.update(cg_data)
                return result
        
        return None
