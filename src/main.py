import time
import sys
from datetime import datetime, timedelta
from src.scanner import Scanner
from src.telegram_sender import TelegramSender
from src.config import ALERT_COOLDOWN_MINUTES

def job(sent_alerts):
    print(f"\nStarting scan at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    scanner = Scanner()
    sender = TelegramSender()
    
    tickers = scanner.get_tickers()
    
    for symbol in tickers:
        try:
            result = scanner.analyze_coin(symbol)
            if result:
                # Check cooldown
                if symbol in sent_alerts:
                    last_alert_time = sent_alerts[symbol]
                    if datetime.now() - last_alert_time < timedelta(minutes=ALERT_COOLDOWN_MINUTES):
                        print(f"Skipping alert for {symbol} (Cooldown active)")
                        continue

                # Update last alert time
                sent_alerts[symbol] = datetime.now()

                # Format Message
                signal_type = result['signal']
                emoji = "🟢" if signal_type == 'LONG' else "🔴"
                
                # Safe formatting
                vol = result['volume_24h']
                if isinstance(vol, (int, float)):
                    vol_str = f"{vol:,.0f} USDT"
                else:
                    vol_str = str(vol)

                fr = result['funding_rate']
                if isinstance(fr, (int, float)):
                    fr_str = f"{fr:.6f}"
                else:
                    fr_str = str(fr)

                message = (
                    f"{emoji} {signal_type} signal detected.\n"
                    f"Coin: {result['symbol']}\n"
                    f"Price: {result['price']}\n"
                    f"RSI: {result['rsi']:.2f}\n"
                    f"MFI: {result['mfi']:.2f}\n"
                    f"VWAP: {result['vwap']:.4f}\n"
                    f"Funding Rate: {fr_str} (Next: {result.get('next_funding', 'N/A')})\n"
                    f"Long/Short Ratio: {result['ls_ratio']}\n"
                    f"24h Volume: {vol_str}\n"
                    f"24h Open Interest: {result['open_interest']}\n"
                    f"--------------------------------\n"
                    f"Market Cap: ${result.get('market_cap', 'N/A'):,.0f}\n"
                    f"Rank: #{result.get('rank', 'N/A')}\n"
                    f"Category: {result.get('categories', 'N/A')}\n"
                    f"Description: {result.get('description', 'N/A')}"
                )
                
                print(f"Sending signal for {symbol}")
                sender.send_message(message)
                
            # Sleep to avoid rate limits
            time.sleep(0.1)
            
        except Exception as e:
            print(f"\nError processing {symbol}: {e}")

    print("\nScan completed.")

def countdown(t):
    while t:
        mins, secs = divmod(t, 60)
        timer = '{:02d}:{:02d}'.format(mins, secs)
        print(f"Next scan in: {timer}", end="\r")
        time.sleep(1)
        t -= 1
    print(" " * 20, end="\r") # Clear line

def main():
    sender = TelegramSender()
    startup_msg = "🚀 rsi_mfi_scanner Bot Started Scanning"
    print(startup_msg)
    sender.send_message(startup_msg)
    
    sent_alerts = {}

    try:
        while True:
            job(sent_alerts)
            
            # Wait 5 minutes with countdown
            wait_seconds = 5 * 60
            print(f"Waiting {wait_seconds/60:.0f} minutes for next scan...")
            countdown(wait_seconds)
            
    except KeyboardInterrupt:
        print("\nBot stopped by user.")
    except KeyboardInterrupt:
        print("\nBot stopped by user.")

if __name__ == "__main__":
    main()
