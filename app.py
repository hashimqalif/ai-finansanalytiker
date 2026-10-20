import os
import streamlit as st
import pandas as pd
from openai import OpenAIError

from ai_engine import FinancialFileError, analyze_report, parse_financial_file
from ai_engine import initiera_supabase, bearbeta_och_spara_finansdata, hamta_historik_fran_supabase

# Sidkonfiguration
st.set_page_config(page_title="Smartare ekonomi | AI-finansanalytiker", page_icon="📈", layout="wide")

# Skapa flikar för Landningssida vs Verktyg
flik_hemsida, flik_verktyg = st.tabs(["🏠 Hem & Prissättning", "🤖 AI-Analysverktyg"])

# =========================================================
# 🏠 FLIK 1: LANDNINGSSIDA & AFFÄRSMODELL
# =========================================================
with flik_hemsida:
    st.title("📈 AI-Finansanalytikern")
    st.markdown("## **Smartare ekonomi. Spårbara beslut.**")
    st.write(
        "Välkommen till framtidens finansiella analys. Vi hjälper CFO:er, företagare "
        "och ekonomer att transformera ostrukturerade rapporter till insiktsfulla beslutsunderlag på sekunder."
    )
    
    st.divider()
    
    st.subheader("Varför välja AI-Finansanalytikern?")
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        st.markdown("### 🤖 Automatiserad precision")
        st.write("Slipp leta i hundrasidiga PDF-filer. Vår AI identifierar och sammanfattar det viktigaste på ett ögonblick.")
    with col_f2:
        st.markdown("### 📈 Visuell historik")
        st.write("Varje siffra du verifierar sparas i en säker molndatabas och förvandlas automatiskt till interaktiva trenddiagram.")
    with col_f3:
        st.markdown("### 🔒 Säkerhet i fokus")
        st.write("Dina finansiella data hanteras i krypterade miljöer. Du har full kontroll över vad som delas och sparas.")

    st.divider()

    st.subheader("Transparent prissättning (Förslag)")
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.info("### **Freemium**\n\n**0 kr** / mån\n\n- 3 analyser / månad\n- Max 5 MB filstorlek\n- Endast lokal analys")
    with col_p2:
        st.success("### **Growth / Pro**\n\n**499 kr** / mån\n\n- Obegränsade analyser\n- Full tillgång till molnhistorik\n- Interaktiva trenddiagram\n- Export till PDF/Excel")
    with col_p3:
        st.warning("### **Enterprise**\n\n**Offereras**\n\n- Custom AI-modeller\n- Direktintegration (SAP/Fortnox)\n- Dedikerad databas\n- Personlig kontoansvarig")

# =========================================================
# 🤖 FLIK 2: DET FAKTISKA AI-VERKTYGET
# =========================================================
with flik_verktyg:
    st.title("📊 AI-finansanalytiker")
    
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        api_key = st.text_input("OpenAI API-nyckel", type="password", key="verktyg_api_key")

    supabase_url = os.environ.get("SUPABASE_URL", "")
    supabase_key = os.environ.get("SUPABASE_ANON_KEY", "")

    uploaded_file = st.file_uploader("Välj en finansiell rapport", type=["csv", "xlsx", "pdf"])

    if uploaded_file is not None:
        st.caption(f"Vald fil: {uploaded_file.name} ({uploaded_file.size / 1024:.1f} KB)")

    if st.button("Analysera rapport", type="primary", disabled=uploaded_file is None or not api_key):
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
                    st.session_state["report_data"] = report

    if st.session_state.get("analysis"):
        st.divider()
        st.subheader(f"Analyse: {st.session_state['analysis_filename']}")
        st.markdown(st.session_state["analysis"])
        
        # 📈 SKARPA DIAGRAM FRÅN SUPABASE
        st.divider()
        st.subheader("📈 Finansiell Trendanalys (Historik från Supabase)")
        
        if supabase_url and supabase_key:
            try:
                sb_client = initiera_supabase(supabase_url, supabase_key)
                db_data = hamta_historik_fran_supabase(sb_client)
                
                if not db_data.empty:
                    graf_col1, graf_col2 = st.columns(2)
                    with graf_col1:
                        st.caption("Omsättningsutveckling (kr)")
                        st.bar_chart(db_data, x="period", y="revenue", color="#1f77b4")
                    with graf_col2:
                        st.caption("Vinst/Förlustutveckling (kr)")
                        st.bar_chart(db_data, x="period", y="profit", color="#2ca02c")
                else:
                    st.info("Databasen är tom. Spara ditt första nyckeltal nedan för att rita diagrammet.")
            except Exception as e:
                st.error(f"Kunde inte hämta diagramdata från Supabase: {str(e)}")
        else:
            st.warning("Supabase är inte konfigurerat. Diagram kan inte ritas från databasen.")

        # DATABASFORMULÄR
        st.divider()
        st.subheader("🗄️ Molndatabas - Spara verifierade nyckeltal")
        col1, col2, col3 = st.columns(3)
        with col1:
            bolagsnamn = st.text_input("Bolagets namn")
        with col2:
            aar = st.number_input("Rapportens år", min_value=2020, max_value=2030, value=2026)
        with col3:
            kvartal = st.selectbox("Period / Kvartal", ["Q1", "Q2", "Q3", "Q4", "Helår"])
            
        col4, col5 = st.columns(2)
        with col4:
            omsattning_input = st.number_input("Faktisk Omsättning (kr)", min_value=0.0)
        with col5:
            vinst_input = st.number_input("Faktisk Vinst/Förlust (kr)", value=0.0)
            
        if st.button("🚀 Spara finansiella data i molnet", type="secondary"):
            if not bolagsnamn:
                st.warning("Du måste fylla i bolagsnamn.")
            elif omsattning_input <= 0:
                st.warning("Omsättningen måste vara större än 0 (Spärr mot nollvärden aktiv).")
            elif not supabase_url or not supabase_key:
                st.info("Logiken validerad! Systemet väntar på skarpa miljövariabler i molnet.")
            else:
                with st.spinner("Sparar nyckeltal..."):
                    try:
                        supabase_klient = initiera_supabase(supabase_url, supabase_key)
                        resultat = bearbeta_och_spara_finansdata(supabase_klient, bolagsnamn, aar, kvartal, omsattning_input, vinst_input)
                        if resultat["status"] == "Success":
                            st.success(resultat["meddelande"])
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(resultat["meddelande"])
                    except Exception as e:
                        st.error(f"Fel: {str(e)}")
