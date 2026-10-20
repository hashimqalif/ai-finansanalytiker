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
    logga_out_anvandare,
)

st.set_page_config(page_title="Smartare ekonomi | AI-finansanalytiker", page_icon="📈", layout="wide")

st.markdown("""
    <style>
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F8FAFC !important;
        color: #1E293B !important;
    }

    [data-testid="stSidebar"] {
        background-color: #0F172A !important;
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] .stCaption {
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

    [data-testid="stMain"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stMain"] h1, [data-testid="stMain"] h2, [data-testid="stMain"] h3,
    [data-testid="stMain"] h4, [data-testid="stMain"] h5, [data-testid="stMain"] h6 {
        color: #1E293B;
    }

    .fintech-brand {
        color: #0284C7 !important;
        font-weight: 800;
    }
    </style>
""", unsafe_allow_html=True)


def hamta_hemlighet(namn: str) -> str:
    """Läser först miljövariabel, sedan Streamlit secrets."""
    varde = os.environ.get(namn, "")
    if varde:
        return varde
    try:
        return str(st.secrets.get(namn, ""))
    except Exception:
        return ""


supabase_url = hamta_hemlighet("SUPABASE_URL")
supabase_key = hamta_hemlighet("SUPABASE_ANON_KEY")
api_key = hamta_hemlighet("OPENAI_API_KEY")

for nyckel, standard in {
    "user_authenticated": False,
    "user_email": None,
    "user_id": None,
    "sb_client": None,
}.items():
    if nyckel not in st.session_state:
        st.session_state[nyckel] = standard

# =========================================================
# SIDEBAR & KONTOSYSTEM
# =========================================================
with st.sidebar:
    st.markdown("## 📈 **AI Finansanalys Pro**")
    st.markdown(
        "<p style='color: #38BDF8; font-weight: bold;'>Smartare ekonomi. Spårbara beslut.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    if not st.session_state["user_authenticated"]:
        st.subheader("🔑 Kundportal")
        konto_val = st.radio("Välj åtgärd", ["Logga in", "Skapa konto"])

        email_input = st.text_input("E-postadress", placeholder="namn@foretag.se")
        password_input = st.text_input("Lösenord", type="password", placeholder="******")

        if not (supabase_url and supabase_key):
            st.error("SUPABASE_URL och SUPABASE_ANON_KEY saknas i Secrets.")

        if konto_val == "Logga in":
            if st.button("Logga in", type="primary", use_container_width=True):
                if email_input and password_input and supabase_url and supabase_key:
                    try:
                        sb = initiera_supabase(supabase_url, supabase_key)
                        res = logga_in_anvandare(sb, email_input, password_input)
                        if res["status"] == "Success":
                            st.session_state["sb_client"] = sb
                            st.session_state["user_authenticated"] = True
                            st.session_state["user_email"] = email_input
                            st.session_state["user_id"] = res["user_id"]
                            st.rerun()
                        else:
                            st.error(res["meddelande"])
                    except Exception as e:
                        st.error(f"Inloggningsfel: {str(e)}")
                else:
                    st.warning("Fyll i e-post och lösenord.")
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
                    st.warning("Fyll i e-post och lösenord.")
    else:
        st.markdown(f"🟢 **Inloggad som:**\n`{st.session_state['user_email']}`")
        if st.button("🔒 Logga ut", use_container_width=True):
            if st.session_state["sb_client"] is not None:
                logga_out_anvandare(st.session_state["sb_client"])
            st.session_state["user_authenticated"] = False
            st.session_state["user_email"] = None
            st.session_state["user_id"] = None
            st.session_state["sb_client"] = None
            st.rerun()

    st.divider()
    st.caption("© 2026 AI-Finansanalytikern AB")

# =========================================================
# HUVUDSIDA
# =========================================================
flik_hemsida, flik_verktyg = st.tabs(["⚡ Premium Dashboard", "🤖 AI-Analysmaskin"])

with flik_hemsida:
    st.markdown("<h1 class='fintech-brand'>Automatisera dina finansiella insikter</h1>", unsafe_allow_html=True)
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
        st.markdown("<div class='premium-card' style='border-top: 4px solid #94A3B8;'><h4>Freemium</h4><h2>0 kr</h2><p>- 3 analyser/mån<br>- Max 5MB filer<br>- Manuell verifiering</p></div>", unsafe_allow_html=True)
    with p_col2:
        st.markdown("<div class='premium-card' style='border-top: 4px solid #0284C7;'><h4>Growth Pro</h4><h2 style='color: #0284C7;'>499 kr</h2><p style='color: #0284C7;'><b>Mest populär</b></p><p>- Obegränsade analyser<br>- Full molnhistorik<br>- Automatiserade KPI-diagram</p></div>", unsafe_allow_html=True)
    with p_col3:
        st.markdown("<div class='premium-card' style='border-top: 4px solid #F59E0B;'><h4>Enterprise</h4><h2>Offereras</h2><p>- Egna AI-modeller<br>- ERP-integrationer (Fortnox)<br>- Dedikerad support</p></div>", unsafe_allow_html=True)

with flik_verktyg:
    if not st.session_state["user_authenticated"]:
        st.markdown("### 🔒 Logga in för att använda AI-Verktyget")
        st.warning("Denna del innehåller konfidentiell datahantering. Vänligen skapa ett konto eller logga in i sidomenyn till vänster för att låsa upp verktyget.")
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
                except (FinancialFileError, ValueError) as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Oväntat fel: {str(e)}")
            else:
                st.warning("Ange en OpenAI API-nyckel först.")

        if "analysis_output" in st.session_state:
            st.divider()
            st.subheader(f"📋 AI-Analysresultat: {st.session_state['analysis_file']}")
            st.markdown(st.session_state["analysis_output"])

        # ---- Spara nyckeltal ----
        st.divider()
        st.subheader("💾 Spara nyckeltal")
        sb_client = st.session_state["sb_client"]

        with st.form("spara_finans_form", clear_on_submit=False):
            c1, c2, c3 = st.columns(3)
            bolagsnamn = c1.text_input("Bolagsnamn")
            aar = c2.number_input("År", min_value=1990, max_value=2100, value=2026, step=1)
            kvartal = c3.selectbox("Kvartal", ["Q1", "Q2", "Q3", "Q4"])
            c4, c5 = st.columns(2)
            omsattning = c4.number_input("Omsättning (kr)", min_value=0.0, value=0.0, step=1000.0)
            vinst = c5.number_input("Vinst/Förlust (kr)", value=0.0, step=1000.0)
            skickat = st.form_submit_button("Spara", type="primary")

        if skickat:
            if not bolagsnamn.strip():
                st.error("Ange bolagsnamn.")
            elif sb_client is None:
                st.error("Ingen aktiv session. Logga ut och in igen.")
            else:
                res = bearbeta_och_spara_finansdata(
                    sb_client, bolagsnamn.strip(), int(aar), kvartal,
                    float(omsattning), float(vinst), st.session_state["user_id"],
                )
                if res["status"] == "Success":
                    st.success(res["meddelande"])
                else:
                    st.error(res["meddelande"])

        # ---- Historik och diagram ----
        st.divider()
        st.subheader("📊 Dina sparade företagsdata")

        db_data = pd.DataFrame()
        if sb_client is not None:
            try:
                db_data = hamta_historik_fran_supabase(sb_client, st.session_state["user_id"])
            except Exception as e:
                st.error(f"Kunde inte ladda historik: {str(e)}")

        if db_data.empty:
            st.info("Ingen data sparad ännu. Fyll i formuläret ovan för att börja bygga din historik.")
        else:
            diagram_data = db_data.set_index("period")
            g1, g2 = st.columns(2)
            with g1:
                st.markdown("**Omsättning och vinst**")
                st.line_chart(diagram_data[["revenue", "profit"]])
            with g2:
                st.markdown("**Vinstmarginal (%)**")
                st.line_chart(diagram_data[["profit_margin"]])

            visa = db_data[["company_name", "period", "revenue", "profit", "profit_margin"]].rename(columns={
                "company_name": "Bolag",
                "period": "Period",
                "revenue": "Omsättning",
                "profit": "Vinst",
                "profit_margin": "Marginal %",
            })
            st.dataframe(visa, use_container_width=True, hide_index=True)
