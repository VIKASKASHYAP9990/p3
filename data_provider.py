import time
import random
import requests
from datetime import datetime
import json
import math

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

# Coordinate mapping for keyless Open-Meteo API
CITY_COORDINATES = {
    "New York": {"lat": 40.7128, "lon": -74.0060},
    "London": {"lat": 51.5074, "lon": -0.1278},
    "Tokyo": {"lat": 35.6762, "lon": 139.6503},
    "Sydney": {"lat": -33.8688, "lon": 151.2093},
    "Paris": {"lat": 48.8566, "lon": 2.3522}
}

# WMO weather code mapping to human-readable weather descriptions
WMO_WEATHER_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear", 2: "Partly Cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing Rime Fog",
    51: "Light Drizzle", 53: "Moderate Drizzle", 55: "Dense Drizzle",
    56: "Light Freezing Drizzle", 57: "Dense Freezing Drizzle",
    61: "Slight Rain", 63: "Moderate Rain", 65: "Heavy Rain",
    66: "Light Freezing Rain", 67: "Heavy Freezing Rain",
    71: "Slight Snowfall", 73: "Moderate Snowfall", 75: "Heavy Snowfall",
    77: "Snow Grains",
    80: "Slight Rain Showers", 81: "Moderate Rain Showers", 82: "Violent Rain Showers",
    85: "Slight Snow Showers", 86: "Heavy Snow Showers",
    95: "Thunderstorm", 96: "Thunderstorm with Hail", 99: "Thunderstorm with Heavy Hail"
}

# Binance symbols mapping
CRYPTO_BINANCE_SYMBOLS = {
    "bitcoin": "BTCUSDT",
    "ethereum": "ETHUSDT",
    "solana": "SOLUSDT",
    "cardano": "ADAUSDT",
    "dogecoin": "DOGEUSDT"
}

# Simulation parameters for Geometric Brownian Motion
# drift represents expected trend, vol represents standard deviation of returns
STOCK_SIM_PARAMS = {
    "AAPL": {"drift": 0.00005, "vol": 0.004},
    "MSFT": {"drift": 0.00007, "vol": 0.003},
    "GOOGL": {"drift": 0.00004, "vol": 0.005},
    "NVDA": {"drift": 0.00015, "vol": 0.008},
    "TSLA": {"drift": -0.00005, "vol": 0.009}
}

CRYPTO_SIM_PARAMS = {
    "bitcoin": {"drift": 0.0001, "vol": 0.007},
    "ethereum": {"drift": 0.00008, "vol": 0.009},
    "solana": {"drift": 0.00015, "vol": 0.012},
    "cardano": {"drift": -0.00005, "vol": 0.015},
    "dogecoin": {"drift": 0.00005, "vol": 0.022}
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

def fetch_binance_crypto_data():
    """
    Fetches cryptocurrency prices and 24h change from Binance API.
    Does not require any API keys.
    """
    symbols_list = list(CRYPTO_BINANCE_SYMBOLS.values())
    url = "https://api.binance.com/api/v3/ticker/24hr"
    params = {
        "symbols": json.dumps(symbols_list, separators=(',', ':'))
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            result = {}
            ticker_map = {ticker["symbol"]: ticker for ticker in data}
            
            for coin_id, symbol in CRYPTO_BINANCE_SYMBOLS.items():
                if symbol in ticker_map:
                    ticker = ticker_map[symbol]
                    price = float(ticker.get("lastPrice", 0.0))
                    change_24h = float(ticker.get("priceChangePercent", 0.0))
                    result[coin_id] = {
                        "name": BASE_CRYPTOS[coin_id]["name"],
                        "symbol": BASE_CRYPTOS[coin_id]["symbol"],
                        "price": price,
                        "change_24h": change_24h,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
            return result
    except Exception as e:
        print(f"Binance API Error: {e}")
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

def fetch_open_meteo_weather(city):
    """
    Fetches weather from Open-Meteo API.
    Does not require any API keys.
    """
    coords = CITY_COORDINATES.get(city)
    if not coords:
        return None
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
    }
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            data = response.json()
            current = data.get("current", {})
            code = current.get("weather_code", 0)
            desc = WMO_WEATHER_CODES.get(code, "Unknown")
            return {
                "temp": current.get("temperature_2m", 0.0),
                "humidity": current.get("relative_humidity_2m", 0),
                "wind": current.get("wind_speed_10m", 0.0),
                "desc": desc,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
    except Exception as e:
        print(f"Open-Meteo API Error for {city}: {e}")
    return None

def get_realtime_data(api_keys=None, history_state=None):
    """
    Main ingestion function that returns current prices and weather.
    If APIs fail or are unconfigured, generates updated simulated data based on history_state.
    
    Tracks source (Binance, Open-Meteo, CoinGecko, simulation) and latency for each feed.
    """
    if api_keys is None:
        api_keys = {}
        
    current_time = datetime.now().strftime("%H:%M:%S")
    timestamp_full = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    status = {}
    
    # ------------------ CRYPTO DATA ------------------
    crypto_data = None
    crypto_source = "simulation"
    crypto_latency = 0
    
    if not api_keys.get("coingecko_disabled", False):
        # Attempt Binance (high reliability, keyless) first if user wants direct API or key isn't provided
        start_t = time.time()
        crypto_data = fetch_binance_crypto_data()
        if crypto_data:
            crypto_source = "Binance API"
            crypto_latency = int((time.time() - start_t) * 1000)
        else:
            # Fallback to CoinGecko
            start_t = time.time()
            crypto_data = fetch_crypto_data(api_keys.get("coingecko"))
            if crypto_data:
                crypto_source = "CoinGecko API"
                crypto_latency = int((time.time() - start_t) * 1000)
                
    if crypto_data is None:
        # Use Geometric Brownian Motion simulation
        crypto_data = {}
        prev_crypto = history_state.get("crypto") if history_state else None
        
        for coin_id, details in BASE_CRYPTOS.items():
            if prev_crypto and coin_id in prev_crypto:
                prev_price = prev_crypto[coin_id]["price"]
                prev_change = prev_crypto[coin_id]["change_24h"]
            else:
                prev_price = details["price"]
                prev_change = random.uniform(-5.0, 5.0)
                
            # GBM step: S_t = S_t-1 * exp((drift - 0.5 * vol^2) * dt + vol * Z)
            params = CRYPTO_SIM_PARAMS.get(coin_id, {"drift": 0.0001, "vol": 0.01})
            drift = params["drift"]
            vol = params["vol"]
            z = random.normalvariate(0, 1)
            
            growth_factor = math.exp((drift - 0.5 * (vol ** 2)) + vol * z)
            new_price = prev_price * growth_factor
            
            # Bound price
            new_price = max(new_price, details["price"] * 0.1)
            
            # Simulated 24h change update
            pct_change = ((new_price - details["price"]) / details["price"]) * 100
            
            crypto_data[coin_id] = {
                "name": details["name"],
                "symbol": details["symbol"],
                "price": new_price,
                "change_24h": pct_change,
                "timestamp": timestamp_full
            }
            
    status["crypto"] = {"source": crypto_source, "latency_ms": crypto_latency}
            
    # ------------------ STOCK DATA ------------------
    stock_data = {}
    prev_stock = history_state.get("stock") if history_state else None
    av_key = api_keys.get("alpha_vantage")
    
    stock_source = "simulation"
    stock_latency = 0
    
    for symbol, details in BASE_STOCKS.items():
        fetched = None
        if av_key:
            start_t = time.time()
            fetched = fetch_stock_data(symbol, av_key)
            if fetched:
                stock_source = "Alpha Vantage API"
                stock_latency = int((time.time() - start_t) * 1000)
                
        if fetched:
            stock_data[symbol] = {
                "name": details["name"],
                "price": fetched["price"],
                "change_24h": fetched["change_24h"],
                "volume": fetched["volume"],
                "timestamp": fetched["timestamp"]
            }
        else:
            # GBM Simulation
            if prev_stock and symbol in prev_stock:
                prev_price = prev_stock[symbol]["price"]
                prev_change = prev_stock[symbol]["change_24h"]
                prev_volume = prev_stock[symbol].get("volume", 1000000)
            else:
                prev_price = details["price"]
                prev_change = random.uniform(-2.0, 2.0)
                prev_volume = random.randint(500000, 5000000)
                
            params = STOCK_SIM_PARAMS.get(symbol, {"drift": 0.00005, "vol": 0.004})
            drift = params["drift"]
            vol = params["vol"]
            z = random.normalvariate(0, 1)
            
            growth_factor = math.exp((drift - 0.5 * (vol ** 2)) + vol * z)
            new_price = prev_price * growth_factor
            new_price = max(new_price, details["price"] * 0.3)
            
            pct_change = ((new_price - details["price"]) / details["price"]) * 100
            new_volume = int(prev_volume * random.uniform(0.95, 1.05))
            
            stock_data[symbol] = {
                "name": details["name"],
                "price": new_price,
                "change_24h": pct_change,
                "volume": new_volume,
                "timestamp": timestamp_full
            }
            
    status["stock"] = {"source": stock_source, "latency_ms": stock_latency}
            
    # ------------------ WEATHER DATA ------------------
    weather_data = {}
    prev_weather = history_state.get("weather") if history_state else None
    owm_key = api_keys.get("openweather")
    
    weather_source = "simulation"
    weather_latency = 0
    
    # Try Open-Meteo first if OWM is not set
    # Or fallback to Open-Meteo if OWM key is invalid
    for city, details in BASE_WEATHER.items():
        fetched = None
        start_t = time.time()
        
        if owm_key:
            fetched = fetch_weather_data(city, owm_key)
            if fetched:
                weather_source = "OpenWeatherMap API"
                weather_latency = int((time.time() - start_t) * 1000)
                
        if fetched is None:
            # Try Open-Meteo (keyless)
            start_t = time.time()
            fetched = fetch_open_meteo_weather(city)
            if fetched:
                weather_source = "Open-Meteo API"
                weather_latency = int((time.time() - start_t) * 1000)
                
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
                
            new_temp = prev_temp + random.uniform(-0.2, 0.2)
            new_temp = max(min(new_temp, 45.0), -15.0)
            
            new_hum = prev_hum + random.randint(-1, 1)
            new_hum = max(min(new_hum, 100), 10)
            
            new_wind = max(0.5, prev_wind + random.uniform(-0.3, 0.3))
            
            new_desc = prev_desc
            if random.random() < 0.03:
                new_desc = random.choice(WEATHER_DESCRIPTIONS)
                
            weather_data[city] = {
                "temp": new_temp,
                "humidity": new_hum,
                "wind": new_wind,
                "desc": new_desc,
                "timestamp": timestamp_full
            }
            
    status["weather"] = {"source": weather_source, "latency_ms": weather_latency}
            
    return {
        "timestamp": current_time,
        "timestamp_full": timestamp_full,
        "crypto": crypto_data,
        "stock": stock_data,
        "weather": weather_data,
        "status": status
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
    Converts list of historical updates into a dict-of-lists suitable for Plotly.
    asset_type: 'crypto', 'stock', or 'weather'
    key: e.g. 'bitcoin' or 'AAPL' or 'London'
    Returns: {"Timestamp": [...], "Value": [...], "TimestampFull": [...]}
    """
    timestamps, values, ts_full = [], [], []
    for item in history_list:
        if asset_type in item and key in item[asset_type]:
            timestamps.append(item["timestamp"])
            val = (item[asset_type][key]["price"]
                   if asset_type != "weather"
                   else item[asset_type][key]["temp"])
            values.append(val)
            ts_full.append(item["timestamp_full"])
    return {"Timestamp": timestamps, "Value": values, "TimestampFull": ts_full}
