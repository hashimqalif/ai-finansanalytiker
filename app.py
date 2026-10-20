import os
import streamlit as st
import pandas as pd
from openai import OpenAIError

from ai_engine import FinancialFileError, analyze_report, parse_financial_file
from ai_engine import (
    initiera_supabase, 
    bearbeta_och_spara_finansdata, 
    hamta_historik_fran_supabase,
    registrera_anvandare,
    logga_in_anvandare,
    logga_out_anvandare
)

# Sidkonfiguration
st.set_page_config(page_title="Smartare ekonomi | AI-finansanalytiker", page_icon="📈", layout="wide")

# Custom CSS för mörkt, lyxigt fintech-tema
st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1A1F2C;
        border-radius: 4px;
        color: #AEB7C6;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00E676 !important;
        color: #0E1117 !important;
        font-weight: bold;
    }
    div[data-testid="metric-container"] {
        background-color: #1A1F2C;
        border: 1px solid #2D3748;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    </style>
""", unsafe_allow_code=True)

# Initiera nycklar
supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_ANON_KEY", "")
api_key = os.environ.get("OPENAI_API_KEY", "")

if "user_authenticated" not in st.session_state:
    st.session_state["user_authenticated"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

# Sidomeny
with st.sidebar:
    st.image("https://icons8.com", width=60)
    st.markdown("## **AI Finansanalys Pro**")
    st.markdown("<p style='color: #00E676; font-weight: bold;'>Smartare ekonomi. Spårbara beslut.</p>", unsafe_allow_code=True)
    st.divider()

    if not st.session_state["user_authenticated"]:
        st.subheader("🔑 Kundportal")
        konto_val = st.radio("Välj åtgärd", ["Logga in", "Skapa konto"])
        
        email_input = st.text_input("E-postadress", placeholder="namn@foretag.se")
        password_input = st.text_input("Lösenord", type="password", placeholder="******")
        
        if konto_val == "Logga in":
            if st.button("Logga in", type="primary", use_container_width=True):
                if email_input and password_input and supabase_url and supabase_key:
                    try:
                        sb = initiera_supabase(supabase_url, supabase_key)
                        res = logga_in_anvandare(sb, email_input, password_input)
                        if res["status"] == "Success":
                            st.session_state["user_authenticated"] = True
                            st.session_state["user_email"] = email_input
                            st.session_state["user_id"] = res["user_id"]
                            st.success("Välkommen tillbaka!")
                            st.rerun()
                        else:
                            st.error(res["meddelande"])
                    except Exception as e:
                        st.error(f"Inloggningsfel: {str(e)}")
        else:
            if st.button("Skapa säkert konto", type="primary", use_container_width=True):
                if email_input and password_input and supabase_url and supabase_key:
                    try:
                        sb = initiera_supabase(supabase_url, supabase_key)
                        res = registrera_anvandare(sb, email_input, password_input)
                        if res["status"] == "Success":
                            st.success("Konto skapat! Du kan nu logga in.")
                        else:
                            st.error(res["meddelande"])
                    except Exception as e:
                        st.error(f"Registreringsfel: {str(e)}")
    else:
        st.markdown(f"🟢 **Inloggad som:**\n`{st.session_state['user_email']}`")
        if st.button("🔒 Logga ut", use_container_width=True):
            st.session_state["user_authenticated"] = False
            st.session_state["user_email"] = None
            st.session_state["user_id"] = None
            st.rerun()

    st.divider()
    st.caption("© 2026 AI-Finansanalytikern AB")

flik_hemsida, flik_verktyg = st.tabs(["⚡ Premium Dashboard", "🤖 AI-Analysmaskin"])

with flik_hemsida:
    st.markdown("<h1 style='color: #00E676;'>Automatisera dina finansiella insikter</h1>", unsafe_allow_code=True)
    st.write("Välkommen till en modern fintech-plattform. Ladda upp ostrukturerade finansiella rapporter (PDF/Excel) och låt vår AI bygga upp din historik.")
    st.divider()
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        st.markdown("### ⚡ Blixtsnabb Extraktion")
        st.info("AI-motorn läser igenom kvartalsrapporter på två sekunder.")
    with f_col2:
        st.markdown("### 🔒 Isolerade Kundkonton")
        st.success("Varje registrerat företag äger sin egen krypterade databasrad.")
    with f_col3:
        st.markdown("### 📈 Visuella Tidsserier")
        st.warning("Värdena ritas omedelbart upp i interaktiva diagram.")

with flik_verktyg:
    if not st.session_state["user_authenticated"]:
        st.markdown("### 🔒 Logga in för att använda AI-Verktyget")
        st.warning("Vänligen skapa ett konto eller logga in i sidomenyn till vänster för att låsa upp verktyget.")
    else:
        st.markdown(f"### 🤖 Välkommen till din AI-analys, `{st.session_state['user_email']}`")
        if not api_key:
            api_key = st.text_input("OpenAI API-nyckel", type="password", key="main_openai_key")
            
        uploaded_file = st.file_uploader("Släpp din finansiella rapport här", type=["csv", "xlsx", "pdf"])
        
        if uploaded_file is not None and st.button("🔥 Starta Djupanalys", type="primary"):
            if api_key:
                try:
                    report = parse_financial_file(uploaded_file.name, uploaded_file.getvalue())
                    analysis = analyze_report(report, api_key)
                    st.session_state["analysis_output"] = analysis
                    st.session_state["analysis_file"] = uploaded_file.name
                except Exception as e:
                    st.error(str(e))
                    
        if "analysis_output" in st.session_state:
            st.divider()
            st.subheader(f"📋 AI-Analysresultat: {st.session_state['analysis_file']}")
            st.markdown(st.session_state["analysis_output"])
            
        st.divider()
        st.subheader("📊 Dina Sparade Företagsdata")
        
        db_data = pd.DataFrame()
        if supabase_url and supabase_key:
            try:
                sb_client = initiera_supabase(supabase_url, supabase_key)
                db_data = hamta_historik_fran_supabase(sb_client, st.session_state["user_id"])
            except Exception as e:
                st.error(f"Kunde inte ladda historik: {str(e)}")
            
        if not db_data.empty:
            senaste_rad = db_data.iloc[-1]
            kpi1, kpi2, kpi3 = st.columns(3)
            with kpi1:
                st.metric("Senaste Omsättning", f"{senaste_rad['revenue']:,.0f} kr")
            with kpi2:
                st.metric("Senaste Vinst/Förlust", f"{senaste_rad['profit']:,.0f} kr")
            with kpi3:
                st.metric("Vinstmarginal", f"{senaste_rad['profit_margin']:.1f} %")
            
            st.write("")
            graf_col1, graf_col2 = st.columns(2)
            with graf_col1:
                st.markdown("**Omsättningstrend per period**")
                st.bar_chart(db_data, x="period", y="revenue", color="#00E676")
            with graf_col2:
                st.markdown("**Resultatutveckling (Vinst/Förlust)**")
                st.bar_chart(db_data, x="period", y="profit", color="#1F77B4")
        else:
            if supabase_url and supabase_key:
                st.info("Din databas är tom. Ange ett nyckeltal nedan för att starta din historik.")
                
        st.divider()
        st.subheader("💾 Spara och verifiera nya nyckeltal")
        col1, col2, col3 = st.columns(3)
        with col1:
            b_namn = st.text_input("Bolagets namn")
        with col2:
            val_aar = st.number_input("År", min_value=2020, max_value=2030, value=2026)
        with col3:
            val_kvartal = st.selectbox("Period", ["Q1", "Q2", "Q3", "Q4", "Helår"])
            
        col4, col5 = st.columns(2)
        with col4:
            rev_input = st.number_input("Verifierad Omsättning (kr)", min_value=0.0)
        with col5:
            prof_input = st.number_input("Verifierad Vinst/Förlust (kr)", value=0.0)
            
        if st.button("🚀 Skicka till min säkra databas", type="secondary"):
            if not b_namn:
                st.warning("Fyll i bolagsnamn.")
            elif rev_input <= 0:
                st.warning("Omsättningen måste vara större än 0.")
            elif supabase_url and supabase_key:
                with st.spinner("Skickar datapaket..."):
                    try:
                        sb_klient = initiera_supabase(supabase_url, supabase_key)
                        resultat = bearbeta_och_spara_finansdata(
                            sb_klient, b_namn, val_aar, val_kvartal, rev_input, prof_input, st.session_state["user_id"]
                        )
                        if resultat["status"] == "Success":
                            st.success(resultat["meddelande"])
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(resultat["meddelande"])
                    except Exception as db_err:
                        st.error(f"Kopplingsfel: {str(db_err)}")
