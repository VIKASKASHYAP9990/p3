import time
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import our custom data provider
import data_provider

# ==========================================
# Page Configuration
# ==========================================
st.set_page_config(
    page_title="Real-Time Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# Custom CSS for Premium Dark UI & Glassmorphism
# ==========================================
st.markdown("""
<style>
    /* Global styles */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Blinking active indicator */
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background-color: #2ecc71;
        margin-right: 8px;
        box-shadow: 0 0 8px #2ecc71;
        animation: blinker 1.5s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0.3; }
    }
    
    /* Custom card styles */
    .glass-card {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-3px);
        border-color: rgba(99, 102, 241, 0.35);
        box-shadow: 0 12px 40px 0 rgba(99, 102, 241, 0.18);
    }
    
    .card-title {
        color: #9ca3af;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
        font-weight: 600;
    }
    
    .card-value {
        color: #ffffff;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 8px;
        letter-spacing: -0.02em;
    }
    
    .card-change {
        font-size: 0.9rem;
        font-weight: 600;
        display: flex;
        align-items: center;
    }
    
    .pos-change {
        color: #10b981;
    }
    
    .neg-change {
        color: #ef4444;
    }
    
    .card-footer {
        color: #6b7280;
        font-size: 0.75rem;
        margin-top: 10px;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
        padding-top: 8px;
    }
    
    /* Alert Banner */
    .alert-banner {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(185, 28, 28, 0.4));
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 20px;
        color: #fca5a5;
        display: flex;
        align-items: center;
        gap: 15px;
        box-shadow: 0 0 15px rgba(239, 68, 68, 0.15);
        animation: pulse-red 2s infinite;
    }
    @keyframes pulse-red {
        0%, 100% { box-shadow: 0 0 15px rgba(239, 68, 68, 0.15); }
        50% { box-shadow: 0 0 25px rgba(239, 68, 68, 0.35); }
    }

    /* API Status indicators styling */
    .status-container {
        display: flex;
        flex-direction: column;
        gap: 6px;
        background: rgba(17, 24, 39, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 12px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    .status-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.8rem;
    }
    .status-name {
        color: #e5e7eb;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    .status-badge {
        font-size: 0.72rem;
        padding: 2px 8px;
        border-radius: 20px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.02em;
    }
    .status-badge.live {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.35);
    }
    .status-badge.sim {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.35);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# Session State Initialization
# ==========================================
if "history" not in st.session_state:
    st.session_state.history = []
if "alerts" not in st.session_state:
    # Default trigger alerts to showcase functionality
    st.session_state.alerts = [
        {"type": "crypto", "key": "bitcoin", "op": ">", "val": 60000.0, "active": True},
        {"type": "stock", "key": "AAPL", "op": ">", "val": 180.0, "active": True},
        {"type": "weather", "key": "London", "op": ">", "val": 14.0, "active": True}
    ]
if "alert_logs" not in st.session_state:
    st.session_state.alert_logs = []
if "owm_key" not in st.session_state:
    st.session_state.owm_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
if "av_key" not in st.session_state:
    st.session_state.av_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True
if "refresh_interval" not in st.session_state:
    st.session_state.refresh_interval = 10
if "temp_unit" not in st.session_state:
    st.session_state.temp_unit = "°C"
if "coingecko_disabled" not in st.session_state:
    st.session_state.coingecko_disabled = False

# ==========================================
# Sidebar UI & Settings
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; color: #6366f1;'>📊 Dashboard Controls</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")

# Data Source & Connections Info
st.sidebar.subheader("🔌 Connection Settings")
with st.sidebar.expander("API Keys Configuration"):
    owm_input = st.text_input("OpenWeatherMap API Key", value=st.session_state.owm_key, type="password", help="Sign up at openweathermap.org for a free key")
    av_input = st.text_input("Alpha Vantage API Key", value=st.session_state.av_key, type="password", help="Sign up at alphavantage.co for a free key")
    
    st.session_state.owm_key = owm_input
    st.session_state.av_key = av_input
    
    # Option to disable CoinGecko if rate-limited
    cg_disabled = st.checkbox("Simulate Crypto (Bypass CoinGecko API)", value=st.session_state.coingecko_disabled, help="Enable this if you hit CoinGecko rate limits")
    st.session_state.coingecko_disabled = cg_disabled

    if st.button("Apply API Config"):
        st.success("API credentials saved to memory!")
        st.rerun()

# Units Configuration
st.sidebar.subheader("🌡️ Visual Customization")
temp_sel = st.sidebar.radio("Temperature Unit", options=["°C", "°F"], index=0 if st.session_state.temp_unit == "°C" else 1)
st.session_state.temp_unit = temp_sel

# Auto Refresh Control
st.sidebar.subheader("⏱️ Live Update Settings")
auto_ref = st.sidebar.checkbox("Enable Live Refresh", value=st.session_state.auto_refresh)
st.session_state.auto_refresh = auto_ref

ref_val = st.sidebar.slider("Rerun Interval (seconds)", min_value=5, max_value=60, value=st.session_state.refresh_interval, step=5)
st.session_state.refresh_interval = ref_val

# Manual Refresh Button
if st.sidebar.button("🔄 Trigger Manual Refresh"):
    st.sidebar.info("Manual refresh triggered.")

# Clear Session
col_clear, col_export = st.sidebar.columns(2)
with col_clear:
    if st.button("🗑️ Clear Cache"):
        st.session_state.history = []
        st.session_state.alert_logs = []
        st.success("Cache cleared!")
        st.rerun()

with col_export:
    if st.session_state.history:
        rows = []
        for snapshot in st.session_state.history:
            ts = snapshot.get("timestamp_full")
            for coin_id, details in snapshot.get("crypto", {}).items():
                rows.append({
                    "Timestamp": ts,
                    "Category": "Crypto",
                    "Asset_City": details.get("name"),
                    "Symbol": details.get("symbol"),
                    "Value": details.get("price"),
                    "Change_24h_Pct": details.get("change_24h"),
                    "Details": "N/A"
                })
            for symbol, details in snapshot.get("stock", {}).items():
                rows.append({
                    "Timestamp": ts,
                    "Category": "Stock",
                    "Asset_City": details.get("name"),
                    "Symbol": symbol,
                    "Value": details.get("price"),
                    "Change_24h_Pct": details.get("change_24h"),
                    "Details": f"Volume: {details.get('volume')}"
                })
            for city, details in snapshot.get("weather", {}).items():
                rows.append({
                    "Timestamp": ts,
                    "Category": "Weather",
                    "Asset_City": city,
                    "Symbol": "N/A",
                    "Value": details.get("temp"),
                    "Change_24h_Pct": 0.0,
                    "Details": f"Humidity: {details.get('humidity')}% | Wind: {details.get('wind')} m/s | Desc: {details.get('desc')}"
                })
        df_export = pd.DataFrame(rows)
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export CSV",
            data=csv_data,
            file_name=f"telemetry_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.button("📥 Export CSV", disabled=True, help="Gather some data points first")

# ----------------- Alert Rules Configuration Form -----------------
st.sidebar.subheader("🚨 Configure Threshold Alerts")
with st.sidebar.form(key="alert_form", clear_on_submit=True):
    alert_type = st.selectbox("Asset Type", ["Crypto", "Stock", "Weather"])
    
    if alert_type == "Crypto":
        keys = list(data_provider.BASE_CRYPTOS.keys())
    elif alert_type == "Stock":
        keys = list(data_provider.BASE_STOCKS.keys())
    else:
        keys = list(data_provider.BASE_WEATHER.keys())
        
    alert_key = st.selectbox("Select Item", keys)
    alert_op = st.selectbox("Condition", [">", "<"])
    alert_val = st.number_input("Threshold Value", value=0.0, format="%.4f")
    
    submit_alert = st.form_submit_button("Add Alert Rule")
    
    if submit_alert:
        new_alert = {
            "type": alert_type.lower(),
            "key": alert_key,
            "op": alert_op,
            "val": alert_val,
            "active": True
        }
        st.session_state.alerts.append(new_alert)
        st.sidebar.success(f"Added Alert: {alert_key} {alert_op} {alert_val}")

# ==========================================
# Data Gathering Step
# ==========================================
api_keys = {
    "openweather": st.session_state.owm_key,
    "alpha_vantage": st.session_state.av_key,
    "coingecko_disabled": st.session_state.coingecko_disabled
}

# Fetch the latest data, referencing the previous run's structure to keep simulation continuity
prev_snapshot = st.session_state.history[-1] if st.session_state.history else None
latest_snapshot = data_provider.get_realtime_data(api_keys=api_keys, history_state=prev_snapshot)

# Update session history list
st.session_state.history = data_provider.update_history(st.session_state.history, latest_snapshot, max_len=30)
current_data = latest_snapshot

# ==========================================
# Alert Checking Logic
# ==========================================
active_alerts_triggered = []
for alert in st.session_state.alerts:
    if not alert.get("active", True):
        continue
    
    a_type = alert["type"]
    a_key = alert["key"]
    op = alert["op"]
    val = alert["val"]
    
    # Get current value
    curr_val = None
    if a_type == "crypto" and a_key in current_data["crypto"]:
        curr_val = current_data["crypto"][a_key]["price"]
    elif a_type == "stock" and a_key in current_data["stock"]:
        curr_val = current_data["stock"][a_key]["price"]
    elif a_type == "weather" and a_key in current_data["weather"]:
        # Standardize temperature unit for comparison based on input
        # Note: API stores Celsius
        curr_val = current_data["weather"][a_key]["temp"]
        if st.session_state.temp_unit == "°F":
            curr_val = data_provider.convert_c_to_f(curr_val)
            
    if curr_val is not None:
        triggered = False
        if op == ">" and curr_val > val:
            triggered = True
        elif op == "<" and curr_val < val:
            triggered = True
            
        if triggered:
            item_display = a_key.upper() if a_type != "weather" else a_key
            val_format = f"{val:.2f}"
            curr_format = f"{curr_val:.2f}"
            unit_sym = "$" if a_type != "weather" else st.session_state.temp_unit
            
            alert_msg = f"{item_display} price/temp crossed alert threshold! Current: {unit_sym}{curr_format} (Rule: {op} {unit_sym}{val_format})"
            active_alerts_triggered.append(alert_msg)
            
            # Log it (de-duplicate consecutive duplicates within last 3 steps)
            log_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            is_duplicate = False
            for log in st.session_state.alert_logs[:3]:
                if log["message"] == alert_msg and (datetime.strptime(log_time, "%Y-%m-%d %H:%M:%S") - datetime.strptime(log["time"], "%Y-%m-%d %H:%M:%S")).seconds < 30:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                st.session_state.alert_logs.insert(0, {
                    "time": log_time,
                    "item": item_display,
                    "type": a_type.upper(),
                    "message": alert_msg
                })

# ==========================================
# Main Dashboard UI Layout
# ==========================================

# 1. Header Banner
col_title, col_status = st.columns([4, 1])
with col_title:
    st.markdown("<h1 style='margin-bottom: 0px;'>📈 Real-Time Data Monitoring System</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #888; font-size: 1.1rem; margin-top: 0px;'>Monitoring crypto market rates, stock tickers, and global meteorological observations.</p>", unsafe_allow_html=True)

with col_status:
    # Display connection mode (API vs Simulation Fallback)
    api_status = current_data.get("status", {})
    
    crypto_src = api_status.get("crypto", {}).get("source", "simulation")
    crypto_lat = api_status.get("crypto", {}).get("latency_ms", 0)
    crypto_badge = f"LIVE ({crypto_lat}ms)" if "API" in crypto_src else "SIMULATION"
    crypto_class = "live" if "API" in crypto_src else "sim"
    
    stock_src = api_status.get("stock", {}).get("source", "simulation")
    stock_lat = api_status.get("stock", {}).get("latency_ms", 0)
    stock_badge = f"LIVE ({stock_lat}ms)" if "API" in stock_src else "SIMULATION"
    stock_class = "live" if "API" in stock_src else "sim"
    
    weather_src = api_status.get("weather", {}).get("source", "simulation")
    weather_lat = api_status.get("weather", {}).get("latency_ms", 0)
    weather_badge = f"LIVE ({weather_lat}ms)" if "API" in weather_src else "SIMULATION"
    weather_class = "live" if "API" in weather_src else "sim"
    
    st.markdown(f"""
    <div class="status-container">
        <div class="status-row">
            <span class="status-name">🪙 Crypto</span>
            <span class="status-badge {crypto_class}">{crypto_badge}</span>
        </div>
        <div class="status-row">
            <span class="status-name">📈 Stocks</span>
            <span class="status-badge {stock_class}">{stock_badge}</span>
        </div>
        <div class="status-row">
            <span class="status-name">🌦️ Weather</span>
            <span class="status-badge {weather_class}">{weather_badge}</span>
        </div>
        <div style="font-size: 0.72rem; color: #6b7280; text-align: center; border-top: 1px solid rgba(255,255,255,0.05); margin-top: 4px; padding-top: 4px;">
            Last: {current_data['timestamp']}
        </div>
    </div>
    """, unsafe_allow_html=True)

# 2. Triggered Alerts Notification Panel
if active_alerts_triggered:
    st.markdown(f"""
    <div class="alert-banner">
        <div style="font-size: 1.8rem;">🚨</div>
        <div>
            <strong style="font-size: 1.1rem;">Active Threshold Alerts Triggered!</strong><br>
            <span style="font-size: 0.95rem;">{'; '.join(active_alerts_triggered)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 3. Main Interface Tabs
tab_markets, tab_weather, tab_alerts = st.tabs([
    "📈 Market Analytics (Stocks & Crypto)", 
    "🌦️ Global Weather Insights", 
    "🚨 Configured Alerts & Logs"
])

# ==========================================
# TAB 1: Markets (Crypto & Stocks)
# ==========================================
with tab_markets:
    st.subheader("🪙 Cryptocurrency Market Feed")
    
    # 5 Column Crypto KPI Row
    crypto_cols = st.columns(5)
    for i, (coin_id, details) in enumerate(current_data["crypto"].items()):
        price = details["price"]
        change_24h = details["change_24h"]
        
        change_class = "pos-change" if change_24h >= 0 else "neg-change"
        arrow = "▲" if change_24h >= 0 else "▼"
        
        with crypto_cols[i]:
            st.markdown(f"""
            <div class="glass-card">
                <div class="card-title">{details['name']} ({details['symbol']})</div>
                <div class="card-value">{data_provider.format_price(price)}</div>
                <div class="card-change {change_class}">
                    <span>{arrow} {data_provider.format_percentage(change_24h)}</span>
                </div>
                <div class="card-footer">
                    Updated: {details['timestamp'].split(' ')[1]}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📊 Stock Quote Feed")
    
    # 5 Column Stock KPI Row
    stock_cols = st.columns(5)
    for i, (symbol, details) in enumerate(current_data["stock"].items()):
        price = details["price"]
        change_24h = details["change_24h"]
        
        change_class = "pos-change" if change_24h >= 0 else "neg-change"
        arrow = "▲" if change_24h >= 0 else "▼"
        
        with stock_cols[i]:
            st.markdown(f"""
            <div class="glass-card">
                <div class="card-title">{details['name']} ({symbol})</div>
                <div class="card-value">{data_provider.format_price(price)}</div>
                <div class="card-change {change_class}">
                    <span>{arrow} {data_provider.format_percentage(change_24h)}</span>
                </div>
                <div class="card-footer">
                    Volume: {details['volume']:,}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    
    # Charts Section
    st.subheader("📈 Real-time Trend Comparison")
    
    col_chart_ctl, col_chart_disp = st.columns([1, 3])
    
    with col_chart_ctl:
        st.markdown("##### Chart Settings")
        chart_asset_type = st.radio("Asset Category", ["Crypto", "Stock"])
        
        if chart_asset_type == "Crypto":
            options = {details["name"]: coin_id for coin_id, details in current_data["crypto"].items()}
        else:
            options = {details["name"]: symbol for symbol, details in current_data["stock"].items()}
            
        selected_asset_name = st.selectbox("Select Asset to Trend", options=list(options.keys()))
        selected_asset_key = options[selected_asset_name]
        
        st.markdown("""
        **Data Processing Features:**
        - **Calculated SMA-5 / SMA-10:** Tracks moving average price over current session.
        - **Daily High/Low:** Records highest & lowest values captured.
        - **Telemetry updates:** New data points stream in real-time.
        """)
        
    with col_chart_disp:
        # Build DataFrame for the selected asset
        df_history = data_provider.history_to_dataframe(
            st.session_state.history, 
            chart_asset_type.lower(), 
            selected_asset_key
        )
        
        if not df_history.empty and len(df_history) >= 2:
            # Calculate Moving Averages (on the fly processing)
            df_history["SMA-5"] = df_history["Value"].rolling(window=5, min_periods=1).mean()
            df_history["SMA-10"] = df_history["Value"].rolling(window=10, min_periods=1).mean()
            
            # Show calculated parameters
            high_val = df_history["Value"].max()
            low_val = df_history["Value"].min()
            volatility = df_history["Value"].std()
            
            cols_stats = st.columns(3)
            cols_stats[0].metric("Session High", data_provider.format_price(high_val))
            cols_stats[1].metric("Session Low", data_provider.format_price(low_val))
            cols_stats[2].metric("Session Volatility (StDev)", f"{volatility:.4f}" if not pd.isna(volatility) else "0.00")
            
            # Create Plotly Chart
            fig = go.Figure()
            
            # Base Asset Line
            fig.add_trace(go.Scatter(
                x=df_history["Timestamp"],
                y=df_history["Value"],
                mode='lines+markers',
                name=selected_asset_name,
                line=dict(color='#6366f1', width=3),
                marker=dict(size=6, color='#6366f1'),
                fill='tozeroy',
                fillcolor='rgba(99, 102, 241, 0.1)'
            ))
            
            # SMA-5 Line
            fig.add_trace(go.Scatter(
                x=df_history["Timestamp"],
                y=df_history["SMA-5"],
                mode='lines',
                name='SMA-5',
                line=dict(color='#10b981', width=2, dash='dash')
            ))
            
            # SMA-10 Line
            fig.add_trace(go.Scatter(
                x=df_history["Timestamp"],
                y=df_history["SMA-10"],
                mode='lines',
                name='SMA-10',
                line=dict(color='#f59e0b', width=2, dash='dot')
            ))
            
            # Overlay active alert thresholds
            active_asset_alerts = [
                a for a in st.session_state.alerts
                if a.get("active", True)
                and a["type"] == chart_asset_type.lower()
                and a["key"] == selected_asset_key
            ]
            for alert in active_asset_alerts:
                op_sym = alert["op"]
                val = alert["val"]
                fig.add_hline(
                    y=val,
                    line_dash="dash",
                    line_color="#ef4444" if op_sym == "<" else "#10b981",
                    annotation_text=f"Alert: {op_sym} ${val:.2f}",
                    annotation_position="bottom right"
                )
            
            fig.update_layout(
                title=f"{selected_asset_name} Price Trend & Moving Averages",
                xaxis_title="Time",
                yaxis_title="Price (USD)",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#ffffff'),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                margin=dict(l=40, r=40, t=40, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Gathering historical data. Plotting line charts requires at least 2 data updates. Please wait for next refresh...")

    st.markdown("---")
    
    # Asset performance comparison chart
    st.subheader("📊 24h Market Return Comparison")
    
    # Calculate dataset
    perf_data = []
    for coin_id, details in current_data["crypto"].items():
        perf_data.append({"Asset": details["symbol"], "Change %": details["change_24h"], "Type": "Crypto"})
    for symbol, details in current_data["stock"].items():
        perf_data.append({"Asset": symbol, "Change %": details["change_24h"], "Type": "Stock"})
        
    df_perf = pd.DataFrame(perf_data)
    
    fig_bar = px.bar(
        df_perf,
        x="Asset",
        y="Change %",
        color="Change %",
        color_continuous_scale=px.colors.diverging.RdYlGn,
        title="Asset 24h Return Percentage Comparison",
        text_auto=".2f"
    )
    fig_bar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#ffffff'),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
        margin=dict(l=40, r=40, t=40, b=40)
    )
    
    st.plotly_chart(fig_bar, use_container_width=True)

# ==========================================
# TAB 2: Weather Insights
# ==========================================
with tab_weather:
    st.subheader("🌦️ Global Meteorological Readings")
    
    weather_cols = st.columns(5)
    for i, (city, details) in enumerate(current_data["weather"].items()):
        temp_c = details["temp"]
        humidity = details["humidity"]
        wind_speed = details["wind"]
        desc = details["desc"]
        
        # Unit conversion
        if st.session_state.temp_unit == "°F":
            temp_display = data_provider.convert_c_to_f(temp_c)
            temp_str = f"{temp_display:.1f}°F"
        else:
            temp_str = f"{temp_c:.1f}°C"
            
        # Select Weather Icon based on description
        icon = "☁️"
        desc_l = desc.lower()
        if "clear" in desc_l or "sunny" in desc_l:
            icon = "☀️"
        elif "cloud" in desc_l:
            icon = "⛅" if "partly" in desc_l else "☁️"
        elif "rain" in desc_l or "shower" in desc_l:
            icon = "🌧️"
        elif "wind" in desc_l:
            icon = "💨"
        elif "storm" in desc_l or "thunder" in desc_l:
            icon = "⚡"
            
        with weather_cols[i]:
            st.markdown(f"""
            <div class="glass-card">
                <div style="font-size: 2.2rem; float: right; margin-top: -5px;">{icon}</div>
                <div class="card-title">{city}</div>
                <div class="card-value">{temp_str}</div>
                <div style="color: #cbd5e1; font-weight: 500; font-size: 0.95rem; margin-bottom: 6px;">{desc}</div>
                <div style="color: #9ca3af; font-size: 0.8rem; display: flex; justify-content: space-between;">
                    <span>💧 Hum: {humidity}%</span>
                    <span>💨 Wind: {wind_speed:.1f} m/s</span>
                </div>
                <div class="card-footer">
                    Updated: {details['timestamp'].split(' ')[1]}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.subheader("📈 Temperature Trend Telemetry")
    col_w_ctl, col_w_chart = st.columns([1, 3])
    
    with col_w_ctl:
        selected_city = st.selectbox("Select City to Graph", options=list(current_data["weather"].keys()))
        st.markdown(f"""
        **City Weather Profile:**
        - **Current Temperature:** {current_data['weather'][selected_city]['temp']:.1f}°C ({data_provider.convert_c_to_f(current_data['weather'][selected_city]['temp']):.1f}°F)
        - **Description:** {current_data['weather'][selected_city]['desc']}
        - **Relative Humidity:** {current_data['weather'][selected_city]['humidity']}%
        - **Wind Velocity:** {current_data['weather'][selected_city]['wind']:.1f} m/s
        """)
        
    with col_w_chart:
        # Build weather dataframe
        df_weather = data_provider.history_to_dataframe(
            st.session_state.history,
            "weather",
            selected_city
        )
        
        if not df_weather.empty and len(df_weather) >= 2:
            # Apply unit conversions to DataFrame if Fahrenheit is selected
            if st.session_state.temp_unit == "°F":
                df_weather["Value"] = df_weather["Value"].apply(data_provider.convert_c_to_f)
                y_label = "Temperature (°F)"
            else:
                y_label = "Temperature (°C)"
                
            fig_weather = go.Figure()
            fig_weather.add_trace(go.Scatter(
                x=df_weather["Timestamp"],
                y=df_weather["Value"],
                mode='lines+markers',
                name=selected_city,
                line=dict(color='#ef4444', width=3),
                marker=dict(size=6, color='#ef4444'),
                fill='tozeroy',
                fillcolor='rgba(239, 68, 68, 0.08)'
            ))
            
            # Overlay active alert thresholds
            active_city_alerts = [
                a for a in st.session_state.alerts
                if a.get("active", True)
                and a["type"] == "weather"
                and a["key"] == selected_city
            ]
            for alert in active_city_alerts:
                op_sym = alert["op"]
                val = alert["val"]
                fig_weather.add_hline(
                    y=val,
                    line_dash="dash",
                    line_color="#ef4444" if op_sym == "<" else "#10b981",
                    annotation_text=f"Alert: {op_sym} {val:.1f}{st.session_state.temp_unit}",
                    annotation_position="bottom right"
                )
            
            fig_weather.update_layout(
                title=f"{selected_city} Temperature Log",
                xaxis_title="Time",
                yaxis_title=y_label,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#ffffff'),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                margin=dict(l=40, r=40, t=40, b=40)
            )
            st.plotly_chart(fig_weather, use_container_width=True)
        else:
            st.info("Gathering weather historical readings. Please wait for a few updates...")

# ==========================================
# TAB 3: Alerts Rules & Logs
# ==========================================
with tab_alerts:
    st.subheader("⚙️ Configured Alert Rules")
    
    if st.session_state.alerts:
        alert_rows = []
        for i, alert in enumerate(st.session_state.alerts):
            item_display = alert['key'].upper() if alert['type'] != 'weather' else alert['key']
            unit_sym = "$" if alert['type'] != 'weather' else st.session_state.temp_unit
            op_disp = "exceeds" if alert['op'] == ">" else "falls below"
            
            status_text = "🟢 Active" if alert.get("active", True) else "🔴 Disabled"
            
            # Action button key
            btn_key = f"toggle_alert_{i}"
            del_key = f"del_alert_{i}"
            
            col_rule, col_stat_act, col_del = st.columns([3, 1, 1])
            with col_rule:
                st.markdown(f"**Rule {i+1}:** Trigger if `{item_display}` {op_disp} **{unit_sym}{alert['val']:.2f}**")
            with col_stat_act:
                if st.button(status_text, key=btn_key):
                    alert["active"] = not alert.get("active", True)
                    st.rerun()
            with col_del:
                if st.button("🗑️ Delete", key=del_key):
                    st.session_state.alerts.pop(i)
                    st.success("Rule deleted.")
                    st.rerun()
            st.markdown("<hr style='margin: 8px 0px; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
    else:
        st.info("No alert rules configured. Configure one in the sidebar panel!")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Alert Trigger Logs
    col_log_title, col_log_clear = st.columns([4, 1])
    with col_log_title:
        st.subheader("📋 Triggered Alerts Historic Logs")
    with col_log_clear:
        if st.button("Clear Log History") and st.session_state.alert_logs:
            st.session_state.alert_logs = []
            st.success("Alert logs cleared!")
            st.rerun()
            
    if st.session_state.alert_logs:
        df_logs = pd.DataFrame(st.session_state.alert_logs)
        # Select and rename columns for display
        df_display = df_logs[["time", "type", "item", "message"]].copy()
        df_display.columns = ["Timestamp", "Category", "Target Item", "Details"]
        
        # Display as a table with custom height
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("No alerts have been triggered yet in this session.")

# ==========================================
# Auto-Refresh Rerun Logic (at the very bottom)
# ==========================================
if st.session_state.auto_refresh:
    # Small countdown visual indicator
    st.sidebar.markdown(f"<p style='text-align: center; color: #888; font-size: 0.85rem;'>Refreshing page in {st.session_state.refresh_interval}s...</p>", unsafe_allow_html=True)
    time.sleep(st.session_state.refresh_interval)
    st.rerun()
