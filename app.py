import os
import streamlit as st
import pandas as pd

from ai_engine import FinancialFileError, analyze_report, parse_financial_file
from ai_engine import (
    initiera_supabase,
    bearbeta_och_spara_finansdata,
    hamta_historik_fran_supabase,
    registrera_anvandare,
    logga_in_anvandare,
)

# 🏢 PREMIUM LIGHT FINTECH THEMING (HÖG KONTRAST & DESIGN)
st.set_page_config(page_title="NQ Trading Bot Portal", page_icon="🤖", layout="wide")

# Custom CSS för ljust, krispigt och supertydligt fintech-tema
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
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
        color: #FFFFFF !important;
    }
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
    div[data-testid="metric-container"], .premium-card {
        background-color: #FFFFFF !important;
        border: 1px solid #E2E8F0 !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03) !important;
    }
    div[data-testid="stMarkdownContainer"] p, h1, h2, h3, h4, h5, h6, label {
        color: #1E293B !important;
    }
    .bot-active { color: #10B981 !important; font-weight: bold; }
    .bot-headline { color: #0284C7 !important; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)


def hamta_hemlighet(namn: str) -> str:
    """Läser först miljövariabel, sedan st.secrets (Streamlit Cloud)."""
    varde = os.environ.get(namn)
    if varde:
        return varde
    try:
        return st.secrets.get(namn, "")
    except Exception:
        return ""


supabase_url = hamta_hemlighet("SUPABASE_URL")
supabase_key = hamta_hemlighet("SUPABASE_ANON_KEY")
api_key = hamta_hemlighet("OPENAI_API_KEY")

for nyckel, standard in [("user_authenticated", False), ("user_email", None), ("user_id", None)]:
    if nyckel not in st.session_state:
        st.session_state[nyckel] = standard

# =========================================================
# 🎛️ SIDOMENY: TRADER PORTAL (KONTO & INLOGGNING)
# =========================================================
with st.sidebar:
    st.markdown("# 🤖")
    st.markdown("## **NQ Trading Bot v1.0**")
    st.markdown(
        "<p style='color: #38BDF8; font-weight: bold;'>Trend & Pullback Automation</p>",
        unsafe_allow_html=True,
    )
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
                    st.warning("Fyll i e-post och lösenord, och kontrollera Supabase-nycklarna.")
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
                    st.warning("Fyll i e-post och lösenord, och kontrollera Supabase-nycklarna.")
    else:
        st.markdown(f"🟢 **Operatör:**\n`{st.session_state['user_email']}`")
        st.markdown("<p class='bot-active'>⚡ Terminal Status: ONLINE</p>", unsafe_allow_html=True)
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
flik_manual, flik_terminal, flik_protokoll = st.tabs(
    ["📚 Byggmanual & Arkitektur", "🤖 Live Trading Terminal", "📋 Bilaga B & D (Checklistor)"]
)

# --- FLIK 1: MANUAL ---
with flik_manual:
    st.markdown("<h1 class='bot-headline'>NQ Trading Bot — Från noll till färdig</h1>", unsafe_allow_html=True)
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
        st.markdown("### 🤖 Robotinställningar & Live-analys")

        aktiv_api_key = api_key
        if not aktiv_api_key:
            aktiv_api_key = st.text_input(
                "OpenAI API-nyckel för nyhetsanalys", type="password", key="bot_openai_key"
            )

        uploaded_log = st.file_uploader(
            "Ladda upp NinjaTrader Logg- eller Backtestfil (CSV/XLSX/PDF)",
            type=["csv", "xlsx", "pdf"],
        )

        if uploaded_log is not None and st.button("🧠 Låt AI Analysera Marknadssentiment", type="primary"):
            if aktiv_api_key:
                try:
                    report = parse_financial_file(uploaded_log.name, uploaded_log.getvalue())
                    with st.spinner("AI utvärderar strategins historiska edge..."):
                        analysis = analyze_report(report, aktiv_api_key)
                        st.session_state["bot_analysis"] = analysis
                except Exception as e:
                    st.error(str(e))
            else:
                st.warning("API-nyckel saknas.")

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
                st.metric("Total Vinst/Förlust", f"{db_data['profit'].sum():,.2f} USD")
            with kpi_t3:
                st.metric("Antal Trades", f"{len(db_data)}")

            st.markdown("#### Ackumulerad avkastning")
            st.line_chart(db_data["profit"].cumsum())

            st.markdown("#### Alla trades")
            st.dataframe(db_data, use_container_width=True)
        else:
            st.info("Ingen exekveringshistorik hittades ännu.")

# --- FLIK 3: CHECKLISTOR ---
with flik_protokoll:
    st.markdown("### 📋 Bilaga B & D (Checklistor)")
    st.info("Platshållare: skicka innehållet i Bilaga B och D så fyller jag i checklistorna.")
