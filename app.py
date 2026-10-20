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

# 🏢 PROFESSIONAL FINTECH THEMING (DARK MODE & CUSTOM STYLES)
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

# Initiera Supabase-anslutning säkert
supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_ANON_KEY", "")
api_key = os.environ.get("OPENAI_API_KEY", "")

# Initiera sessionshantering säkert
if "user_authenticated" not in st.session_state:
    st.session_state["user_authenticated"] = False
if "user_email" not in st.session_state:
    st.session_state["user_email"] = None
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None

# =========================================================
# 🎛️ SIDEBAR & KONTOSYSTEM
# =========================================================
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
                if email_input and password_input:
                    if supabase_url and supabase_key:
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
                        st.warning("System: Databasnycklar saknas i inställningarna.")
                else:
                    st.warning("Vänligen fyll i både e-post och lösenord.")
        else:
            if st.button("Skapa säkert konto", type="primary", use_container_width=True):
                if email_input and password_input:
                    if supabase_url and supabase_key:
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
                        st.warning("System: Databasnycklar saknas i inställningarna.")
                else:
                    st.warning("Vänligen fyll i både e-post och lösenord.")
    else:
        st.markdown(f"🟢 **Inloggad som:**\n`{st.session_state['user_email']}`")
        st.caption("Ditt konto är helt isolerat och krypterat.")
        if st.button("🔒 Logga ut", use_container_width=True):
            try:
                if supabase_url and supabase_key:
                    sb = initiera_supabase(supabase_url, supabase_key)
                    logga_out_anvandare(sb)
            except Exception:
                pass
            st.session_state["user_authenticated"] = False
            st.session_state["user_email"] = None
            st.session_state["user_id"] = None
            st.rerun()

    st.divider()
    st.caption("© 2026 AI-Finansanalytikern AB")

# =========================================================
# 🏠 HUVUDSIDA: FLIKAR FÖR HEMSIIDA VS VERKTYG
# =========================================================
flik_hemsida, flik_verktyg = st.tabs(["⚡ Premium Dashboard", "🤖 AI-Analysmaskin"])

# --- FLIK 1: LANDNINGSSIDA ---
with flik_hemsida:
    st.markdown("<h1 style='color: #00E676;'>Automatisera dina finansiella insikter</h1>", unsafe_allow_code=True)
    st.markdown("### *Generativ AI möter molnbaserad tidsserieanalys.*")
    st.write(
        "Välkommen till en modern fintech-plattform. Ladda upp ostrukturerade finansiella "
        "rapporter (PDF/Excel) och låt vår AI bygga upp din historik, råda om vinstmarginal och analysera risker automatiskt."
    )
    st.divider()
    
    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        st.markdown("### ⚡ Blixtsnabb Extraktion")
        st.info("Sluta leta manuellt. Vår AI-motor läser igenom kvartalsrapporter på två sekunder och lyfter ut kärndatan.")
    with f_col2:
        st.markdown("### 🔒 Isolerade Kundkonton")
        st.success("Varje registrerat företag äger sin egen krypterade databasrad. Din finansiella data kan aldrig läcka till obehöriga.")
    with f_col3:
        st.markdown("### 📈 Visuella Tidsserier")
        st.warning("De verifierade värdena ritas omedelbart upp i interaktiva diagram som visar tillväxt, trender och lönsamhet.")

    st.divider()
    st.subheader("💎 Flexibla medlemskap för tillväxt (Förslag)")
    p_col1, p_col2, p_col3 = st.columns(3)
    with p_col1:
        st.markdown("<div style='background-color: #1A1F2C; padding: 20px; border-radius: 10px; border-left: 5px solid #AEB7C6;'><h4>Freemium</h4><h2>0 kr</h2><p>- 3 analyser/mån<br>- Max 5MB filer<br>- Manuell verifiering</p></div>", unsafe_allow_code=True)
    with p_col2:
        st.markdown("<div style='background-color: #1A1F2C; padding: 20px; border-radius: 10px; border-left: 5px solid #00E676;'><h4>Growth Pro</h4><h2>499 kr</h2><p style='color: #00E676;'><b>Mest populär</b></p><p>- Obegränsade analyser<br>- Full molnhistorik<br>- Automatiserade KPI-diagram</p></div>", unsafe_allow_code=True)
    with p_col3:
        st.markdown("<div style='background-color: #1A1F2C; padding: 20px; border-radius: 10px; border-left: 5px solid #FFB300;'><h4>Enterprise</h4><h2>Offereras</h2><p>- Egna AI-modeller<br>- ERP-integrationer (Fortnox)<br>- Dedikerad support</p></div>", unsafe_allow_code=True)

# --- FLIK 2: VERKTYG (INLOGGNINGSKRAV) ---
with flik_verktyg:
    if not st.session_state["user_authenticated"]:
        st.markdown("### 🔒 Logga in för att använda AI-Verktyget")
        st.warning("Denna del innehåller konfidentiell datahantering. Vänligen skapa ett konto eller logga in i sidomenyn till vänster för att låsa upp verktyget.")
    else:
        st.markdown(f"### 🤖 Välkommen till din AI-analys, `{st.session_state['user_email']}`")
        if not api_key:
            api_key = st.text_input("OpenAI API-nyckel", type="password", key="main_openai_key")
            
        uploaded_file = st.file_uploader("Släpp din finansiella rapport här (PDF, CSV, XLSX)", type=["csv", "xlsx", "pdf"])
        
        if uploaded_file is not None:
            if st.button("🔥 Starta Djupanalys", type="primary"):
                if api_key:
                    try:
                        report = parse_financial_file(uploaded_file.name, uploaded_file.getvalue())
                        with st.spinner("AI-motorn analyserar rapporten..."):
                            analysis = analyze_report(report, api_key)
                            st.session_state["analysis_output"] = analysis
                            st.session_state["analysis_file"] = uploaded_file.name
                    except Exception as e:
                        st.error(str(e))
                else:
                    st.warning("Vänligen ange din OpenAI API-nyckel för att köra analysen.")
                    
        if "analysis_output" in st.session_state:
            st.divider()
            st.subheader(f"📋 AI-Analysresultat: {st.session_state['analysis_file']}")
            st.markdown(st.session_state["analysis_output"])
            
        # 📊 INTERAKTIVA DIAGRAM FRÅN SUPABASE
        st.divider()
        st.subheader("📊 Dina Sparade Företagsdata")
        
        if supabase_url and supabase_key:
            db_data = pd.DataFrame()
            try:
