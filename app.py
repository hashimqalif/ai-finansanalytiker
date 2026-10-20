import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# 🏢 PREMIUM LIGHT FINTECH CONFIGURATION (ÖPPEN TERMINAL)
st.set_page_config(page_title="NQ Trading Bot Terminal", page_icon="🤖", layout="wide")

# Custom CSS för krispigt, ljust premium-tema med hög kontrast
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F8FAFC !important;
        color: #1E293B !important;
    }
    [data-testid="stSidebar"] { 
        background-color: #0F172A !important; 
        color: #FFFFFF !important; 
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label { 
        color: #FFFFFF !important; 
    }
    div[data-testid="metric-container"], .premium-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
    }
    div[data-testid="stMarkdownContainer"] p, h1, h2, h3, h4, h5, h6, label { 
        color: #1E293B !important; 
    }
    .signal-box { padding: 15px; border-radius: 8px; font-weight: bold; text-align: center; margin-bottom: 20px; }
    .long-sig { background-color: #DCFCE7; color: #15803D; border: 2px solid #22C55E; }
    .short-sig { background-color: #FEE2E2; color: #B91C1C; border: 2px solid #EF4444; }
    .neutral-sig { background-color: #F1F5F9; color: #475569; border: 2px solid #94A3B8; }
    </style>
""", unsafe_allow_html=True)

# =========================================================
# 🎛️ REALTIME SIMULATOR ENGINE (Marknadsdata)
# =========================================================
if "market_data" not in st.session_state:
    # Generera 60 startpunkter för NQ-indexet runt 20 000 punkter
    np.random.seed(42)
    base_price = 20000.0
    times = pd.date_range(end=pd.Timestamp.now(), periods=60, freq='5min')
    data = []
    
    for t in times:
        move = np.random.normal(0, 15)
        base_price += move
        open_p = base_price - np.random.uniform(-10, 10)
        close_p = base_price + np.random.uniform(-10, 10)
        high_p = max(open_p, close_p) + np.random.uniform(0, 15)
        low_p = min(open_p, close_p) - np.random.uniform(0, 15)
        data.append([t, open_p, high_p, low_p, close_p])
        
    st.session_state["market_data"] = pd.DataFrame(data, columns=["Time", "Open", "High", "Low", "Close"])

# Beräkna indikatorer live utifrån din handbok
df = st.session_state["market_data"].copy()
df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()
df["VWAP"] = df["Close"].expanding().mean() + 2
df["TR"] = np.maximum(df["High"] - df["Low"], np.maximum(abs(df["High"] - df["Close"].shift(1)), abs(df["Low"] - df["Close"].shift(1))))
df["ATR"] = df["TR"].rolling(window=14).mean().fillna(20.0)

latest = df.iloc[-1]
is_long_trend = latest["EMA20"] > latest["EMA50"]
is_short_trend = latest["EMA20"] < latest["EMA50"]
is_long_bias = latest["Close"] > latest["VWAP"]
is_short_bias = latest["Close"] < latest["VWAP"]
is_long_pullback = latest["Low"] <= latest["EMA20"] and latest["Close"] > latest["EMA20"]
is_short_pullback = latest["High"] >= latest["EMA20"] and latest["Close"] < latest["EMA20"]

# =========================================================
# 🎛️ SIDOMENY (KONTROLLER)
# =========================================================
with st.sidebar:
    st.markdown("# 🤖")
    st.markdown("## **NQ Live Terminal**")
    st.markdown("<p style='color: #38BDF8; font-weight: bold;'>Status: LIVE & OPERATIV</p>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown("### 🎛️ Marknadssimulering")
    if st.button("🔄 Generera Ny Bar (Tick)", type="primary", use_container_width=True):
        new_time = df["Time"].iloc[-1] + pd.Timedelta(minutes=5)
        last_close = df["Close"].iloc[-1]
        move = np.random.normal(0, 15)
        new_close = last_close + move
        new_open = last_close
        new_high = max(new_open, new_close) + np.random.uniform(0, 12)
        new_low = min(new_open, new_close) - np.random.uniform(0, 12)
        
        new_row = pd.DataFrame([[new_time, new_open, new_high, new_low, new_close]], columns=["Time", "Open", "High", "Low", "Close"])
        st.session_state["market_data"] = pd.concat([st.session_state["market_data"], new_row]).iloc[1:].reset_index(drop=True)
        st.rerun()

    if st.button("♻️ Nollställ Diagram", use_container_width=True):
        del st.session_state["market_data"]
        st.rerun()

    st.divider()
    st.caption("Exklusiv privat utgåva v1.0")

# =========================================================
# 🏠 HUVUDSIDA: LIVE-TERMINAL & STRATEGI
# =========================================================
st.markdown("<h1 style='color: #0284C7; font-weight: 800;'>🤖 Min Personliga NQ Trading Bot</h1>", unsafe_allow_html=True)
st.write("Terminalen körs helt lokalt i din session. Inga inloggningar krävs.")
st.divider()

# Live-statistik för de exakta reglerna
col_k1, col_l2, col_k3, col_k4 = st.columns(4)
with col_k1: st.metric("NQ Live Pris", f"{latest['Close']:.2f} USD")
with col_l2: st.metric("EMA 20 / 50 Trend", "🟢 BULLISH (Long)" if is_long_trend else "🔴 BEARISH (Short)")
with col_k3: st.metric("VWAP Bias", "🟢 OVER VWAP" if is_long_bias else "🔴 UNDER VWAP")
with col_k4: st.metric("ATR Volatilitet", f"{latest['ATR']:.1f}")

# --- 🚦 AUTOMATISK SIGNALAVKÄNNING ---
st.write("")
if is_long_trend and is_long_bias and is_long_pullback:
    st.markdown("<div class='signal-box long-sig'>🟢 KÖPSIGNAL IDENTIFIERAD: ENTER LONG (EMA Pullback + Confirmation slutförd)</div>", unsafe_allow_html=True)
elif is_short_trend and is_short_bias and is_short_pullback:
    st.markdown("<div class='signal-box short-sig'>🔴 SÄLJSIGNAL IDENTIFIERAD: ENTER SHORT (EMA Pullback + Confirmation slutförd)</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='signal-box neutral-sig'>⚪ MARKNADSSCANNER: Söker efter regelbunden Pullback mot EMA 20...</div>", unsafe_allow_html=True)

# --- 📈 PROFESSIONELLT CANDLESTICK-DIAGRAM ---
st.subheader("📈 Interaktiv 5-Minutersgraf (NQ Futures)")
fig = go.Figure()

# Lägg till Candlesticks
fig.add_trace(go.Candlestick(x=df['Time'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='NQ Pris'))
# Lägg till dina indikatorer
fig.add_trace(go.Scatter(x=df['Time'], y=df['EMA20'], line=dict(color='#22C55E', width=1.5), name='EMA 20 (Fast Pullback)'))
fig.add_trace(go.Scatter(x=df['Time'], y=df['EMA50'], line=dict(color='#1E3A8A', width=1.5), name='EMA 50 (Slow Trend)'))
fig.add_trace(go.Scatter(x=df['Time'], y=df['VWAP'], line=dict(color='#38BDF8', width=2, dash='dash'), name='Sessions-VWAP'))

fig.update_layout(template="plotly_white", xaxis_rangeslider_visible=False, height=550, margin=dict(l=10, r=10, t=10, b=10))
st.plotly_chart(fig, use_container_width=True)

# --- 📋 CHECKLISTOR ---
st.divider()
st.subheader("📋 Snabba Kontroller (Från Handboken)")
c1, c2 = st.columns(2)
with c1:
    st.checkbox("NinjaTrader 8 ansluten till live-feed")
    st.checkbox("Strategi kompilerad med 0 fel")
with c2:
    st.checkbox("Daily Loss Limit aktiverad i C#")
    st.checkbox("Emergency-stop-knappen är testad")
