import requests
import time

class CoinGeckoManager:
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.coin_map = {}
        self.last_update = 0
        self.update_interval = 86400 # Update map once a day
        
        # Cache for coin details: {coin_id: (data, timestamp)}
        self.details_cache = {}
        self.cache_duration = 3600 # 1 hour cache for details
        
    def update_coin_map(self):
        """Fetch coin list and create a symbol -> id map"""
        try:
            # Check if update is needed
            if time.time() - self.last_update < self.update_interval and self.coin_map:
                return

            print("Updating CoinGecko coin list...")
            url = f"{self.base_url}/coins/list"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # Create map: symbol (lowercase) -> id
                # Note: There are duplicates (e.g. multiple coins with symbol 'ETH'). 
                # We usually take the one with highest rank, but this list doesn't have rank.
                # We'll just take the first one or try to match exact names if possible.
                # For better accuracy, we might need to check 'coins/markets' but that's heavy.
                # Let's stick to simple mapping for now.
                self.coin_map = {item['symbol'].lower(): item['id'] for item in data}
                self.last_update = time.time()
                print("CoinGecko map updated.")
            else:
                print(f"Failed to fetch CoinGecko list: {response.status_code}")
        except Exception as e:
            print(f"Error updating CoinGecko map: {e}")

    def get_coin_details(self, symbol):
        """Get coin details by symbol (e.g., BTC)"""
        self.update_coin_map()
        
        # Clean symbol (e.g. BTC/USDT -> btc)
        base_symbol = symbol.split('/')[0].lower()
        
        coin_id = self.coin_map.get(base_symbol)
        if not coin_id:
            # Try some common fixes
            if base_symbol == '1000pepe': coin_id = 'pepe'
            # Add more manual mappings if needed
            
        if not coin_id:
            return None

        # Check cache
        if coin_id in self.details_cache:
            cached_data, timestamp = self.details_cache[coin_id]
            if time.time() - timestamp < self.cache_duration:
                return cached_data

        try:
            url = f"{self.base_url}/coins/{coin_id}"
            params = {
                'localization': 'true',
                'tickers': 'false',
                'market_data': 'true',
                'community_data': 'false',
                'developer_data': 'false',
                'sparkline': 'false'
            }
            
            # Single request with timeout, no retries
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                description = data.get('description', {}).get('en', '')
                if not description:
                    description = 'Description not found.'
                
                # Truncate description if too long
                if len(description) > 500:
                    description = description[:497] + "..."

                result = {
                    'market_cap': data.get('market_data', {}).get('market_cap', {}).get('usd', 0),
                    'rank': data.get('market_cap_rank', 'N/A'),
                    'categories': ", ".join(data.get('categories', [])),
                    'description': description
                }
                
                # Save to cache
                self.details_cache[coin_id] = (result, time.time())
                return result
                
            elif response.status_code == 429:
                print("CoinGecko Rate Limit Hit! Skipping.")
                return {
                    'market_cap': 'N/A',
                    'rank': 'N/A',
                    'categories': 'N/A',
                    'description': '⚠️ CoinGecko Rate Limit Hit (Skipped)'
                }
            else:
                print(f"CoinGecko API Error: {response.status_code}")
                return {
                    'market_cap': 'N/A',
                    'rank': 'N/A',
                    'categories': 'N/A',
                    'description': f'⚠️ CoinGecko Error: {response.status_code}'
                }
            
        except Exception as e:
            print(f"Error fetching CoinGecko details: {e}")
            return {
                'market_cap': 'N/A',
                'rank': 'N/A',
                'categories': 'N/A',
                'description': '⚠️ CoinGecko Connection Error'
            }
