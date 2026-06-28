# Real-Time Data Analytics Dashboard

This project is a highly polished, interactive, real-time telemetry dashboard built using **Streamlit** and **Plotly**. It simulates monitoring systems in real-world contexts, tracking cryptocurrency prices, stock market quotes, and global meteorological observations.

## Features

1. **Multi-Source Real-Time Telemetry:**
   * **Cryptocurrencies:** Bitcoin (BTC), Ethereum (ETH), Solana (SOL), Cardano (ADA), Dogecoin (DOGE). Fetched via CoinGecko API.
   * **Stock Market Tickers:** Apple (AAPL), Microsoft (MSFT), Alphabet (GOOGL), NVIDIA (NVDA), Tesla (TSLA). Fetched via Alpha Vantage API.
   * **Meteorological Stations:** Weather for New York, London, Tokyo, Sydney, Paris. Fetched via OpenWeatherMap API.
2. **Adaptive Simulation Engine:**
   * If you do not have API keys for Alpha Vantage or OpenWeatherMap, or if you hit CoinGecko API rate limits, the system automatically falls back to generating state-driven real-time fluctuations (random walks), ensuring immediate out-of-the-box interactivity.
3. **Advanced Visual Styling:**
   * Dark-themed glassmorphism cards.
   * Dynamically color-coded metrics indicators showing positive and negative 24h market trends.
   * Smooth, interactive time-series plots with calculated 5-point and 10-point moving averages (SMA-5, SMA-10) and session volatility indicators.
4. **Triggered Threshold Alerts:**
   * User-customizable rule settings directly from the sidebar.
   * Immediate visual warning alerts at the top of the dashboard when a threshold is breached.
   * Historic logs list tracking all triggered alert actions.
5. **Configurable Live Update Loop:**
   * Choose to pause/play automatic page refresh and customize update rerun intervals (from 5s to 60s).

## Project Structure

* `app.py`: Main dashboard script defining the UI layout, styling, tab controls, alerts, and update loops.
* `data_provider.py`: Handles connections to REST APIs, filters and maps response data, handles errors, and simulates stream telemetries.
* `requirements.txt`: Python package dependencies.
* `.env.template`: Key settings template file.

## Getting Started

### 1. Installation
Ensure you have Python 3.8+ installed. Install the dependencies via:
```bash
pip install -r requirements.txt
```

### 2. Configure API Keys (Optional)
To use real API data:
1. Copy `.env.template` to `.env` in the project root:
   ```bash
   cp .env.template .env
   ```
2. Open `.env` and fill in your API keys:
   * **OpenWeatherMap Key:** Register for a free key at [OpenWeatherMap](https://openweathermap.org/).
   * **Alpha Vantage Key:** Register for a free key at [Alpha Vantage](https://www.alphavantage.co/).

*Alternatively, you can input these keys directly in the sidebar expansion menu of the dashboard UI.*

### 3. Launching the Dashboard
Start the Streamlit server from your terminal:
```bash
streamlit run app.py
```
This will start a local web server (usually at `http://localhost:8501`) and automatically open it in your browser.
