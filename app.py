import os
import streamlit as st
import pandas as pd

from ai_engine import FinancialFileError, analyze_report, parse_financial_file
from ai_engine import (
    initiera_supabase, 
    bearbeta_och_spara_finansdata, 
    hamta_historik_fran_supabase,
    registrera_anvandare,
    logga_in_anvandare
)

# 🏢 PREMIUM LIGHT FINTECH THEMING (HÖG KONTRAST & DESIGN)
st.set_page_config(page_title="NQ Trading Bot Portal", page_icon="🤖", layout="wide")

# Custom CSS för ljust, krispigt och supertydligt fintech-tema (10/10 läsbarhet)
st.markdown("""
    <style>
    /* Ljus och fräsch bakgrund */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F8FAFC !important;
        color: #1E293B !important;
    }
    
    /* Mörkblå professionell sidomeny för fintech-kontrast */
    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }
    
    /* Snygga flikar */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: #E2E8F0;
        padding: 6px;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 6px;
        color: #475569;
        padding: 8px 16px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        font-weight: bold;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Vita instrumentkort med subtila skuggor */
    div[data-testid="metric-container"], .premium-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03) !important;
    }
    
    /* Säkra textkontraster */
    div[data-testid="stMarkdownContainer"] p, h1, h2, h3, h4, h5, h6, label {
        color: #1E293B !important;
    }
    
    .bot-active {
        color: #10B981 !important;
        font-weight: bold;
    }
    .bot-headline {
        color: #0284C7 !important;
        font-weight: 800;
    }
    </style>
""", unsafe_allow_code=True)

# Initiera nycklar från Secrets
supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_ANON_KEY", "")
api_key = os.environ.get("OPENAI_API_KEY", "")

if "user_authenticated" not in st.session_state:
    st.session_state["user_authenticated"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

# =========================================================
# 🎛️ SIDOMENY: TRADER PORTAL (KONTO & INLOGGNING)
# =========================================================
with st.sidebar:
    st.image("https://icons8.com", width=60)
    st.markdown("## **NQ Trading Bot v1.0**")
    st.markdown("<p style='color: #38BDF8; font-weight: bold;'>Trend & Pullback Automation</p>", unsafe_allow_code=True)
    st.divider()

    if not st.session_state["user_authenticated"]:
        st.subheader("🔐 Trader-autentisering")
        konto_val = st.radio("Välj funktion", ["Logga in", "Skapa konto"])
        
        email_input = st.text_input("E-postadress", placeholder="trader@firma.se")
        password_input = st.text_input("Lösenord", type="password", placeholder="******")
        
        if konto_val == "Logga in":
            if st.button("Öppna kontrollpanel", type="primary", use_container_width=True):
                if email_input and password_input and supabase_url and supabase_key:
                    try:
                        sb = initiera_supabase(supabase_url, supabase_key)
                        res = logga_in_anvandare(sb, email_input, password_input)
                        if res["status"] == "Success":
                            st.session_state["user_authenticated"] = True
                            st.session_state["user_email"] = email_input
                            st.session_state["user_id"] = res["user_id"]
                            st.success("Ansluten till algoterminalen!")
                            st.rerun()
                        else:
                            st.error(res["meddelande"])
                    except Exception as e:
                        st.error(f"Kopplingsfel: {str(e)}")
        else:
            if st.button("Registrera ny bot-licens", type="primary", use_container_width=True):
                if email_input and password_input and supabase_url and supabase_key:
                    try:
                        sb = initiera_supabase(supabase_url, supabase_key)
                        res = registrera_anvandare(sb, email_input, password_input)
                        if res["status"] == "Success":
                            st.success("Konto registrerat! Logga in ovan.")
                        else:
                            st.error(res["meddelande"])
                    except Exception as e:
                        st.error(f"Registreringsfel: {str(e)}")
    else:
        st.markdown(f"🟢 **Operatör:**\n`{st.session_state['user_email']}`")
        st.markdown("<p class='bot-active'>⚡ Terminal Status: ONLINE</p>", unsafe_allow_code=True)
        if st.button("🔒 Koppla ifrån terminal", use_container_width=True):
            st.session_state["user_authenticated"] = False
            st.session_state["user_email"] = None
            st.session_state["user_id"] = None
            st.rerun()

    st.divider()
    st.caption("© 2026 Algorithmic Systems AB")

# =========================================================
# 🏠 HUVUDSIDA: HANDBOK VS TERMINAL
# =========================================================
flik_manual, flik_terminal, flik_protokoll = st.tabs(["📚 Byggmanual & Arkitektur", "🤖 Live Trading Terminal", "📋 Bilaga B & D (Checklistor)"])

# --- FLIK 1: MANUAL ---
with flik_manual:
    st.markdown("<h1 class='bot-headline'>NQ Trading Bot — Från noll till färdig</h1>", unsafe_allow_code=True)
    st.markdown("### *Automatiserad Trend & Pullback-strategi för NQ/MNQ Futures.*")
    st.write("Denna manual guidar dig steg-för-steg genom skapandet av en regelbaserad tradingrobot för NinjaTrader 8.")
    st.divider()
    
    col_spec1, col_spec2, col_spec3 = st.columns(3)
    with col_spec1:
        st.markdown("### 📊 Marknad & Hårdvara")
        st.info("**Instrument:** NQ / MNQ Futures\n\n**Timeframe:** 5 minuter\n\n**Plattform:** NinjaTrader 8 (NinjaScript)")
    with col_spec2:
        st.markdown("### ⚙️ Indikatorer & Filter")
        st.success("**Trend:** EMA 20 > EMA 50\n\n**Filter:** Pris jämfört med VWAP\n\n**Sizing:** ATR-baserad stop & target")
    with col_spec3:
        st.markdown("### 🔒 Live Riskskydd")
        st.warning("**Daily Lock:** Spärr vid maxförlust\n\n**Positioner:** Max 1 aktiv position\n\n**Order:** OnBarClose-verifiering")

    st.divider()
    st.subheader("🧮 Kontraktsöversikt")
    m_col1, m_col2 = st.columns(2)
    with m_col1:
        st.markdown("<div class='premium-card' style='border-top: 4px solid #0284C7;'><h4>E-mini Nasdaq-100 (NQ)</h4><h2>$20 / punkt</h2><p><b>Minsta tick:</b> 0.25 punkter ($5)</p></div>", unsafe_allow_html=True)
    with m_col2:
        st.markdown("<div class='premium-card' style='border-top: 4px solid #10B981;'><h4>Micro E-mini Nasdaq-100 (MNQ)</h4><h2>$2 / punkt</h2><p><b>Minsta tick:</b> 0.25 punkter ($0.50)</p></div>", unsafe_allow_html=True)

# --- FLIK 2: HANDELSTERMINAL ---
with flik_terminal:
    if not st.session_state["user_authenticated"]:
        st.markdown("### 🔒 Algoritmisk Panel Låst")
        st.warning("Vänligen logga in eller skapa konto i sidomenyn till vänster för att öppna live-terminalen.")
    else:
        st.markdown(f"### 🤖 Robotinställningar & Live-analys")
        if not api_key:
            api_key = st.text_input("OpenAI API-nyckel för nyhetsanalys", type="password", key="bot_openai_key")
            
        uploaded_log = st.file_uploader("Ladda upp NinjaTrader Logg- eller Backtestfil (CSV/PDF)", type=["csv", "xlsx", "pdf"])
        
        if uploaded_log is not None and st.button("🧠 Låt AI Analysera Marknadssentiment", type="primary"):
            if api_key:
                try:
                    report = parse_financial_file(uploaded_log.name, uploaded_log.getvalue())
                    with st.spinner("AI utvärderar strategins historiska edge..."):
                        analysis = analyze_report(report, api_key)
                        st.session_state["bot_analysis"] = analysis
                except Exception as e:
                    st.error(str(e))
                    
        if "bot_analysis" in st.session_state:
            st.divider()
            st.subheader("📋 AI Strategi- & Riskrapport")
            st.markdown(st.session_state["bot_analysis"])
            
        st.divider()
        st.subheader("📊 Robotens Exekveringshistorik (Från Supabase)")
        
        db_data = pd.DataFrame()
        if supabase_url and supabase_key:
            try:
                sb_client = initiera_supabase(supabase_url, supabase_key)
                db_data = hamta_historik_fran_supabase(sb_client, st.session_state["user_id"])
            except Exception as e:
                st.error(f"Kunde inte hämta robotdata: {str(e)}")
        
        if not db_data.empty:
            senaste_trade = db_data.iloc[-1]
            kpi_t1, kpi_t2, kpi_t3 = st.columns(3)
            with kpi_t1:
                st.metric("Senaste Trade-Resultat", f"{senaste_trade['profit']:,.2f} USD")
            with kpi_t2:
