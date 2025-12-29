import time
import schedule
from datetime import datetime
from src.scanner import Scanner
from src.telegram_sender import TelegramSender

def job():
    print(f"Starting scan at {datetime.now()}")
    scanner = Scanner()
    sender = TelegramSender()
    
    tickers = scanner.get_tickers()
    
    for symbol in tickers:
        try:
            result = scanner.analyze_coin(symbol)
            if result:
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
                    f"{emoji} {signal_type} sinyali alındı.\n"
                    f"Coin Adı: {result['symbol']}\n"
                    f"Fiyat: {result['price']}\n"
                    f"RSI Değeri: {result['rsi']:.2f}\n"
                    f"MFI Değeri: {result['mfi']:.2f}\n"
                    f"VWAP: {result['vwap']:.4f}\n"
                    f"Funding Rate: {fr_str}\n"
                    f"Long/Short Ratio: {result['ls_ratio']}\n"
                    f"24 h Volume: {vol_str}\n"
                    f"24 h Open Interest: {result['open_interest']}"
                )
                
                print(f"Sending signal for {symbol}")
                sender.send_message(message)
                
            # Sleep to avoid rate limits
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    print("Scan completed.")

def main():
    print("Bot started. Waiting for next scan...")
    try:
        # Run immediately on start
        job()
        
        # Schedule every 15 minutes
        schedule.every(15).minutes.do(job)
        
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nBot stopped by user.")

if __name__ == "__main__":
    main()
