import time
import random
import requests
import pandas as pd
from datetime import datetime

# Base prices and configs for fallback simulation
BASE_STOCKS = {
    "AAPL": {"price": 182.50, "name": "Apple Inc."},
    "MSFT": {"price": 421.90, "name": "Microsoft Corp."},
    "GOOGL": {"price": 176.40, "name": "Alphabet Inc."},
    "NVDA": {"price": 122.10, "name": "NVIDIA Corp."},
    "TSLA": {"price": 185.00, "name": "Tesla Inc."}
}

BASE_CRYPTOS = {
    "bitcoin": {"price": 64200.0, "name": "Bitcoin", "symbol": "BTC"},
    "ethereum": {"price": 3480.0, "name": "Ethereum", "symbol": "ETH"},
    "solana": {"price": 148.50, "name": "Solana", "symbol": "SOL"},
    "cardano": {"price": 0.48, "name": "Cardano", "symbol": "ADA"},
    "dogecoin": {"price": 0.14, "name": "Dogecoin", "symbol": "DOGE"}
}

BASE_WEATHER = {
    "New York": {"temp": 22.5, "desc": "Partly Cloudy", "humidity": 60, "wind": 4.5},
    "London": {"temp": 15.2, "desc": "Light Rain", "humidity": 82, "wind": 6.2},
    "Tokyo": {"temp": 26.8, "desc": "Clear Sky", "humidity": 55, "wind": 2.1},
    "Sydney": {"temp": 18.4, "desc": "Windy", "humidity": 68, "wind": 8.5},
    "Paris": {"temp": 20.1, "desc": "Sunny", "humidity": 50, "wind": 3.8}
}

WEATHER_DESCRIPTIONS = ["Clear Sky", "Sunny", "Partly Cloudy", "Mostly Cloudy", "Light Rain", "Moderate Rain", "Windy"]

def convert_c_to_f(temp_c):
    """Converts temperature from Celsius to Fahrenheit."""
    return (temp_c * 9/5) + 32

def format_price(value, symbol="$"):
    """Formats numeric value to currency style string."""
    if value is None:
        return "N/A"
    if value < 1.0:
        return f"{symbol}{value:.4f}"
    return f"{symbol}{value:,.2f}"

def format_percentage(value):
    """Formats numeric value to percentage string."""
    if value is None:
        return "0.00%"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"

def fetch_crypto_data(api_key=None):
    """
    Fetches real-time cryptocurrency data from CoinGecko.
    If the API fails or is rate-limited, returns None to trigger fallback.
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids": ",".join(BASE_CRYPTOS.keys()),
        "vs_currencies": "usd",
        "include_24hr_change": "true"
    }
    
    headers = {}
    if api_key:
        headers["x-cg-demo-api-key"] = api_key
        # Pro API or Demo API endpoints might differ slightly, but we use demo key header
        
    try:
        response = requests.get(url, params=params, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            result = {}
            for coin_id, details in BASE_CRYPTOS.items():
                if coin_id in data:
                    price = data[coin_id].get("usd")
                    change_24h = data[coin_id].get("usd_24h_change", 0.0)
                    result[coin_id] = {
                        "name": details["name"],
                        "symbol": details["symbol"],
                        "price": price,
                        "change_24h": change_24h,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
            return result
    except Exception as e:
        print(f"CoinGecko API Error: {e}")
    return None

def fetch_stock_data(symbol, api_key):
    """
    Fetches stock data from Alpha Vantage.
    Requires an API Key. Returns None if key is missing or request fails.
    """
    if not api_key:
        return None
    
    url = "https://www.alphavantage.co/query"
    params = {
        "function": "GLOBAL_QUOTE",
        "symbol": symbol,
        "apikey": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            quote = data.get("Global Quote", {})
            if quote:
                price = float(quote.get("05. price", 0.0))
                change_percent_str = quote.get("10. change percent", "0.0%").replace("%", "")
                change_24h = float(change_percent_str) if change_percent_str else 0.0
                volume = int(quote.get("06. volume", 0))
                return {
                    "price": price,
                    "change_24h": change_24h,
                    "volume": volume,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
    except Exception as e:
        print(f"Alpha Vantage API Error for {symbol}: {e}")
    return None

def fetch_weather_data(city, api_key):
    """
    Fetches weather data from OpenWeatherMap.
    Requires an API Key. Returns None if key is missing or request fails.
    """
    if not api_key:
        return None
    
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            main = data.get("main", {})
            wind = data.get("wind", {})
            weather_desc = data.get("weather", [{}])[0].get("description", "Unknown").title()
            
            return {
                "temp": main.get("temp", 0.0),
                "humidity": main.get("humidity", 0),
                "wind": wind.get("speed", 0.0),
                "desc": weather_desc,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    except Exception as e:
        print(f"OpenWeatherMap API Error for {city}: {e}")
    return None

def get_realtime_data(api_keys=None, history_state=None):
    """
    Main ingestion function that returns current prices and weather.
    If APIs fail or are unconfigured, generates updated simulated data based on history_state.
    
    history_state should be a dict containing previous data to compute fluctuations.
    """
    if api_keys is None:
        api_keys = {}
        
    current_time = datetime.now().strftime("%H:%M:%S")
    timestamp_full = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # ------------------ CRYPTO DATA ------------------
    crypto_data = None
    if not api_keys.get("coingecko_disabled", False):
        crypto_data = fetch_crypto_data(api_keys.get("coingecko"))
        
    if crypto_data is None:
        # Use simulation fallback
        crypto_data = {}
        prev_crypto = history_state.get("crypto") if history_state else None
        
        for coin_id, details in BASE_CRYPTOS.items():
            # Get previous price
            if prev_crypto and coin_id in prev_crypto:
                prev_price = prev_crypto[coin_id]["price"]
                prev_change = prev_crypto[coin_id]["change_24h"]
            else:
                prev_price = details["price"]
                prev_change = random.uniform(-5.0, 5.0)
                
            # Random walk fluctuation (-1.5% to +1.5%)
            change_pct = random.uniform(-0.015, 0.015)
            new_price = prev_price * (1 + change_pct)
            
            # Bound price to prevent collapsing to zero
            new_price = max(new_price, details["price"] * 0.2)
            
            # Simple calculated 24h change updating
            new_change = prev_change + (change_pct * 100)
            new_change = max(min(new_change, 20.0), -20.0) # Clamp
            
            crypto_data[coin_id] = {
                "name": details["name"],
                "symbol": details["symbol"],
                "price": new_price,
                "change_24h": new_change,
                "timestamp": timestamp_full
            }
            
    # ------------------ STOCK DATA ------------------
    stock_data = {}
    prev_stock = history_state.get("stock") if history_state else None
    av_key = api_keys.get("alpha_vantage")
    
    for symbol, details in BASE_STOCKS.items():
        fetched = None
        if av_key:
            fetched = fetch_stock_data(symbol, av_key)
            
        if fetched:
            stock_data[symbol] = {
                "name": details["name"],
                "price": fetched["price"],
                "change_24h": fetched["change_24h"],
                "volume": fetched["volume"],
                "timestamp": fetched["timestamp"]
            }
        else:
            # Fallback Simulation
            if prev_stock and symbol in prev_stock:
                prev_price = prev_stock[symbol]["price"]
                prev_change = prev_stock[symbol]["change_24h"]
                prev_volume = prev_stock[symbol].get("volume", 1000000)
            else:
                prev_price = details["price"]
                prev_change = random.uniform(-2.0, 2.0)
                prev_volume = random.randint(500000, 5000000)
                
            # Fluctuate (-0.8% to +0.8%)
            change_pct = random.uniform(-0.008, 0.008)
            new_price = prev_price * (1 + change_pct)
            new_price = max(new_price, details["price"] * 0.5)
            
            new_change = prev_change + (change_pct * 100)
            new_change = max(min(new_change, 10.0), -10.0)
            
            new_volume = int(prev_volume * random.uniform(0.9, 1.1))
            
            stock_data[symbol] = {
                "name": details["name"],
                "price": new_price,
                "change_24h": new_change,
                "volume": new_volume,
                "timestamp": timestamp_full
            }
            
    # ------------------ WEATHER DATA ------------------
    weather_data = {}
    prev_weather = history_state.get("weather") if history_state else None
    owm_key = api_keys.get("openweather")
    
    for city, details in BASE_WEATHER.items():
        fetched = None
        if owm_key:
            fetched = fetch_weather_data(city, owm_key)
            
        if fetched:
            weather_data[city] = {
                "temp": fetched["temp"],
                "humidity": fetched["humidity"],
                "wind": fetched["wind"],
                "desc": fetched["desc"],
                "timestamp": fetched["timestamp"]
            }
        else:
            # Fallback Simulation
            if prev_weather and city in prev_weather:
                prev_temp = prev_weather[city]["temp"]
                prev_desc = prev_weather[city]["desc"]
                prev_hum = prev_weather[city]["humidity"]
                prev_wind = prev_weather[city]["wind"]
            else:
                prev_temp = details["temp"]
                prev_desc = details["desc"]
                prev_hum = details["humidity"]
                prev_wind = details["wind"]
                
            # Fluctuate temp by +/- 0.3°C
            new_temp = prev_temp + random.uniform(-0.3, 0.3)
            # Clip temperatures to reasonable ranges
            new_temp = max(min(new_temp, 45.0), -15.0)
            
            # Fluctuate humidity by +/- 2%
            new_hum = prev_hum + random.randint(-2, 2)
            new_hum = max(min(new_hum, 100), 10)
            
            # Fluctuate wind by +/- 0.5 m/s
            new_wind = max(0.5, prev_wind + random.uniform(-0.5, 0.5))
            
            # 5% chance to change description
            new_desc = prev_desc
            if random.random() < 0.05:
                new_desc = random.choice(WEATHER_DESCRIPTIONS)
                
            weather_data[city] = {
                "temp": new_temp,
                "humidity": new_hum,
                "wind": new_wind,
                "desc": new_desc,
                "timestamp": timestamp_full
            }
            
    return {
        "timestamp": current_time,
        "timestamp_full": timestamp_full,
        "crypto": crypto_data,
        "stock": stock_data,
        "weather": weather_data
    }

def update_history(history_list, latest_data, max_len=30):
    """
    Appends the latest data snapshot to a list of historical updates.
    Maintains max_len size.
    """
    if history_list is None:
        history_list = []
        
    history_list.append(latest_data)
    if len(history_list) > max_len:
        history_list.pop(0)
        
    return history_list

def history_to_dataframe(history_list, asset_type, key):
    """
    Converts list of historical updates into a pandas DataFrame suitable for plotting.
    asset_type: 'crypto', 'stock', or 'weather'
    key: e.g. 'bitcoin' or 'AAPL' or 'London'
    """
    data_points = []
    for item in history_list:
        if asset_type in item and key in item[asset_type]:
            data_points.append({
                "Timestamp": item["timestamp"],
                "Value": item[asset_type][key]["price"] if asset_type != "weather" else item[asset_type][key]["temp"],
                "TimestampFull": item["timestamp_full"]
            })
            
    return pd.DataFrame(data_points)
