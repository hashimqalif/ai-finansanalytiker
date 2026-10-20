import os
from datetime import date

import httpx
import streamlit as st
from openai import OpenAIError
from postgrest.exceptions import APIError

from ai_engine import (
    FinancialFileError,
    analyze_report,
    bearbeta_och_spara_finansdata,
    initiera_supabase,
    parse_financial_file,
)


st.set_page_config(page_title="AI-finansanalytiker", page_icon="📊", layout="wide")
st.title("AI-finansanalytiker")
st.write(
    "Ladda upp en finansiell rapport för att få en strukturerad sammanfattning av "
    "siffror, utveckling och osäkerheter."
)

st.info(
    "Integritet: Filen behandlas i den här appen. När du begär en analys skickas "
    "det extraherade rapportinnehållet till OpenAI för behandling."
)

api_key = os.environ.get("OPENAI_API_KEY", "")
if not api_key:
    api_key = st.text_input(
        "OpenAI API-nyckel",
        type="password",
        help="Nyckeln används endast under den här sessionen och sparas inte av appen.",
    )

uploaded_file = st.file_uploader(
    "Välj en finansiell rapport",
    type=["csv", "xlsx", "pdf"],
    help="Max 10 MB. PDF-filer måste innehålla text, inte bara skannade bilder.",
)

if uploaded_file is not None:
    st.caption(f"Vald fil: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")

if st.button(
    "Analysera rapport",
    type="primary",
    disabled=uploaded_file is None or not api_key,
):
    try:
        report = parse_financial_file(uploaded_file.name, uploaded_file.getvalue())
    except FinancialFileError as error:
        st.error(str(error))
    else:
        with st.spinner("Analyserar rapporten …"):
            try:
                analysis = analyze_report(report, api_key)
            except OpenAIError as error:
                st.error(f"OpenAI-analysen misslyckades: {error}")
            else:
                st.session_state["analysis"] = analysis
                st.session_state["analysis_filename"] = uploaded_file.name
                st.session_state["analysis_details"] = report.details
                st.session_state["analysis_notice"] = report.notice

if uploaded_file is None:
    st.caption("Ladda upp en CSV-, Excel- eller PDF-fil för att komma igång.")
elif not api_key:
    st.warning("Ange en OpenAI API-nyckel för att starta analysen.")

if st.session_state.get("analysis"):
    st.divider()
    st.subheader(f"Analys: {st.session_state['analysis_filename']}")
    st.caption(st.session_state["analysis_details"])
    if st.session_state.get("analysis_notice"):
        st.warning(st.session_state["analysis_notice"])
    st.markdown(st.session_state["analysis"])
    st.caption(
        "Analysen är automatisk och kan innehålla fel. Kontrollera siffrorna mot "
        "originalkällan; detta är inte personlig investeringsrådgivning."
    )

st.divider()
st.subheader("Spara finansiella nyckeltal i Supabase")
st.caption(
    "Ange verifierade värden från rapporten. De hämtas inte automatiskt från "
    "AI-analysen."
)

bolagsnamn = st.text_input("Bolagsnamn")
period_col1, period_col2 = st.columns(2)
with period_col1:
    aar = st.number_input(
        "År",
        min_value=1,
        max_value=date.today().year + 1,
        value=date.today().year,
        step=1,
    )
with period_col2:
    kvartal = st.selectbox("Kvartal", ["Q1", "Q2", "Q3", "Q4"])

value_col1, value_col2 = st.columns(2)
with value_col1:
    omsattning_input = st.number_input(
        "Omsättning",
        min_value=0.0,
        value=0.0,
        step=1_000.0,
        help="Ange rapportens omsättning; värdet måste vara större än noll.",
    )
with value_col2:
    vinst_input = st.number_input(
        "Vinst",
        value=0.0,
        step=1_000.0,
        help="Ange rapportens vinst. Ett negativt värde kan anges för förlust.",
    )

supabase_url = os.environ.get("SUPABASE_URL", "")
supabase_key = os.environ.get("SUPABASE_KEY", "")

if st.button("🚀 Spara finansiella data i molnet", type="secondary"):
    if not bolagsnamn.strip():
        st.warning("Du måste fylla i bolagsnamn.")
    elif omsattning_input <= 0:
        st.warning(
            "Omsättningen måste vara större än 0 för att kunna beräkna "
            "vinstmarginal och spara."
        )
    elif not supabase_url or not supabase_key:
        st.error(
            "Systemfel: Anslutningsnycklar för Supabase saknas i "
            "miljövariablerna SUPABASE_URL och SUPABASE_KEY."
        )
    else:
        with st.spinner("Ansluter till molndatabasen och sparar nyckeltal..."):
            try:
                supabase_klient = initiera_supabase(supabase_url, supabase_key)
                resultat = bearbeta_och_spara_finansdata(
                    supabase_klient,
                    bolagsnamn,
                    int(aar),
                    kvartal,
                    omsattning_input,
                    vinst_input,
                )
            except (APIError, httpx.HTTPError, ValueError) as error:
                st.error(f"Kunde inte spara till Supabase: {error}")
            else:
                if resultat["status"] == "Success":
                    st.success(resultat["meddelande"])
                    st.balloons()
                else:
                    st.error(resultat["meddelande"])