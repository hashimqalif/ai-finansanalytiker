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

st.set_page_config(
    page_title="Finansanalytikern | AI-driven ekonomianalys",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================================================
# DESIGN
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, .stApp, [class*="css"] {
    font-family: 'Inter', -apple-system, 'Segoe UI', sans-serif !important;
}
.stApp { background: #F6F8FC !important; }

/* Dölj Streamlits standardgränssnitt */
#MainMenu, footer, [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], [data-testid="stSidebar"],
[data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}
header[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
.block-container { max-width: 1180px !important; padding-top: 1rem !important; padding-bottom: 4rem !important; }

/* Navigering (flikar) */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px; background: #FFFFFF; padding: 6px; border-radius: 14px;
    border: 1px solid #E3E8F0; box-shadow: 0 1px 2px rgba(15,23,42,.04);
}
.stTabs [data-baseweb="tab"] {
    height: 44px; padding: 0 22px; border-radius: 10px; background: transparent;
    color: #475569; font-weight: 600; font-size: 15px;
}
.stTabs [aria-selected="true"] { background: #0B1B3A !important; color: #FFFFFF !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none !important; }

/* Topprad */
.topbar { display:flex; align-items:center; justify-content:space-between; padding: 14px 4px 18px 4px; }
.brand { display:flex; align-items:center; gap:12px; }
.brand-logo {
    width:40px; height:40px; border-radius:11px; display:flex; align-items:center; justify-content:center;
    background: linear-gradient(135deg,#2563EB,#14B8A6); color:#fff; font-size:20px; font-weight:800;
}
.brand-name { font-size:20px; font-weight:800; color:#0B1B3A; letter-spacing:-.3px; }
.brand-sub { font-size:12px; color:#64748B; margin-top:-2px; }
.top-pill { font-size:13px; font-weight:600; color:#0B1B3A; background:#E8F0FE; padding:7px 14px; border-radius:999px; }

/* Hero */
.hero {
    background: radial-gradient(1200px 400px at 85% -10%, rgba(20,184,166,.35), transparent 60%),
                radial-gradient(900px 500px at 0% 110%, rgba(37,99,235,.45), transparent 60%),
                #0B1B3A;
    border-radius: 24px; padding: 72px 56px; margin: 22px 0 26px 0; position: relative; overflow: hidden;
}
.hero .badge {
    display:inline-block; font-size:13px; font-weight:600; color:#BFD6FF;
    background: rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.15);
    padding:7px 14px; border-radius:999px; margin-bottom:22px;
}
.hero h1 { font-size:52px !important; line-height:1.08 !important; font-weight:800 !important; color:#FFFFFF !important; letter-spacing:-1.2px; margin:0 0 18px 0 !important; padding:0 !important; }
.hero h1 span { background: linear-gradient(90deg,#60A5FA,#2DD4BF); -webkit-background-clip:text; background-clip:text; color:transparent !important; -webkit-text-fill-color: transparent; }
.hero p { font-size:19px; line-height:1.6; color:#CBD5E1 !important; max-width:640px; margin:0 0 6px 0 !important; }
.hero .hint { font-size:15px; color:#93C5FD !important; margin-top:22px !important; font-weight:600; }

/* Nyckeltalsrad */
.stats { display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:46px; }
.stat { background:#fff; border:1px solid #E3E8F0; border-radius:16px; padding:22px; text-align:center; box-shadow:0 1px 2px rgba(15,23,42,.04); }
.stat b { display:block; font-size:26px; font-weight:800; color:#0B1B3A; letter-spacing:-.5px; }
.stat span { font-size:13.5px; color:#64748B; }

/* Sektioner */
.sec-head { text-align:center; margin: 18px 0 30px 0; }
.sec-head .eyebrow { font-size:13px; font-weight:700; color:#2563EB; letter-spacing:1.4px; text-transform:uppercase; }
.sec-head h2 { font-size:34px !important; font-weight:800 !important; color:#0B1B3A !important; letter-spacing:-.8px; margin:8px 0 10px 0 !important; padding:0 !important; }
.sec-head p { font-size:17px; color:#64748B !important; max-width:620px; margin:0 auto !important; }

.grid3 { display:grid; grid-template-columns:repeat(3,1fr); gap:20px; margin-bottom:56px; }
.card { background:#fff; border:1px solid #E3E8F0; border-radius:18px; padding:28px; box-shadow:0 1px 2px rgba(15,23,42,.04); transition: all .2s ease; }
.card:hover { transform: translateY(-3px); box-shadow:0 14px 30px -12px rgba(15,23,42,.18); border-color:#CBD8F0; }
.card .ico { width:46px; height:46px; border-radius:12px; background:#E8F0FE; display:flex; align-items:center; justify-content:center; font-size:22px; margin-bottom:16px; }
.card h3 { font-size:18px !important; font-weight:700 !important; color:#0B1B3A !important; margin:0 0 8px 0 !important; padding:0 !important; }
.card p { font-size:15px; line-height:1.6; color:#64748B !important; margin:0 !important; }

.step-num { width:38px; height:38px; border-radius:50%; background:#0B1B3A; color:#fff; font-weight:700; display:flex; align-items:center; justify-content:center; margin-bottom:16px; }

/* Priser */
.price { background:#fff; border:1px solid #E3E8F0; border-radius:20px; padding:34px 30px; box-shadow:0 1px 2px rgba(15,23,42,.04); position:relative; }
.price.pop { border:2px solid #2563EB; box-shadow:0 20px 40px -18px rgba(37,99,235,.35); }
.price .tag { position:absolute; top:-13px; left:50%; transform:translateX(-50%); background:#2563EB; color:#fff; font-size:12px; font-weight:700; padding:5px 14px; border-radius:999px; }
.price h4 { font-size:17px !important; font-weight:700 !important; color:#0B1B3A !important; margin:0 0 10px 0 !important; }
.price .amount { font-size:42px; font-weight:800; color:#0B1B3A; letter-spacing:-1px; }
.price .amount small { font-size:15px; font-weight:500; color:#64748B; letter-spacing:0; }
.price ul { list-style:none; padding:0; margin:22px 0 0 0; }
.price li { font-size:15px; color:#334155; padding:8px 0; border-top:1px solid #EEF2F7; }
.price li:before { content:"✓"; color:#14B8A6; font-weight:800; margin-right:10px; }

/* Inloggningskort */
.login-title { font-size:26px; font-weight:800; color:#0B1B3A; letter-spacing:-.5px; margin-bottom:4px; }
.login-sub { font-size:15px; color:#64748B; margin-bottom:10px; }

/* KPI-kort */
[data-testid="stMetric"] {
    background:#fff; border:1px solid #E3E8F0; border-radius:16px; padding:20px 22px;
    box-shadow:0 1px 2px rgba(15,23,42,.04);
}
[data-testid="stMetricLabel"] { color:#64748B !important; font-weight:600; }
[data-testid="stMetricValue"] { color:#0B1B3A !important; font-weight:800; letter-spacing:-.5px; }

/* Knappar och inputs */
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
    border-radius:11px !important; font-weight:600 !important; padding:10px 22px !important;
    border:1px solid #D5DCE8 !important; transition: all .15s ease;
}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"],
.stButton > button[kind="primaryFormSubmit"], .stFormSubmitButton > button[kind="primaryFormSubmit"] {
    background:#2563EB !important; color:#fff !important; border:1px solid #2563EB !important;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button:hover { filter:brightness(1.08); transform:translateY(-1px); }
.stTextInput input, .stNumberInput input { border-radius:10px !important; }
[data-testid="stFileUploader"] section { border-radius:14px !important; border:2px dashed #C5D3EA !important; background:#FBFCFE !important; }
[data-testid="stExpander"] { background:#fff; border:1px solid #E3E8F0 !important; border-radius:14px !important; }

.result-card { background:#fff; border:1px solid #E3E8F0; border-left:5px solid #2563EB; border-radius:14px; padding:22px 26px; margin-top:14px; }
.footer { margin-top:70px; padding:34px 0 10px 0; border-top:1px solid #E3E8F0; text-align:center; color:#64748B; font-size:14px; line-height:1.8; }
.footer b { color:#0B1B3A; }

@media (max-width: 900px) {
    .hero { padding: 44px 26px; } .hero h1 { font-size: 34px !important; }
    .grid3 { grid-template-columns: 1fr; } .stats { grid-template-columns: repeat(2,1fr); }
}
</style>
""", unsafe_allow_html=True)


def h(html: str) -> None:
    """Visar HTML. Tar bort indrag så att Markdown inte tolkar raderna som kod."""
    st.markdown("".join(rad.strip() for rad in html.splitlines()), unsafe_allow_html=True)


def hamta_hemlighet(namn: str) -> str:
    """Läser först miljövariabel, sedan Streamlit secrets."""
    varde = os.environ.get(namn, "")
    if varde:
        return varde
    try:
        return str(st.secrets.get(namn, ""))
    except Exception:
        return ""


def kr(v) -> str:
    return f"{v:,.0f} kr".replace(",", " ")


def procent_forandring(nu, innan):
    if innan in (0, None) or pd.isna(innan):
        return None
    return (nu - innan) / abs(innan) * 100


supabase_url = hamta_hemlighet("SUPABASE_URL")
supabase_key = hamta_hemlighet("SUPABASE_ANON_KEY")
api_key = hamta_hemlighet("OPENAI_API_KEY")

for nyckel, standard in {
    "user_authenticated": False,
    "user_email": None,
    "user_id": None,
    "sb_client": None,
    "flash": None,
}.items():
    if nyckel not in st.session_state:
        st.session_state[nyckel] = standard


# =========================================================
# TOPPRAD
# =========================================================
status_text = (
    f"🟢 {st.session_state['user_email']}" if st.session_state["user_authenticated"] else "Kundportal"
)
h(f"""
<div class="topbar">
  <div class="brand">
    <div class="brand-logo">F</div>
    <div>
      <div class="brand-name">Finansanalytikern</div>
      <div class="brand-sub">AI-driven ekonomianalys</div>
    </div>
  </div>
  <div class="top-pill">{status_text}</div>
</div>
""")

flik_hem, flik_priser, flik_verktyg = st.tabs(["Hem", "Priser", "Analysverktyget"])

# =========================================================
# HEM
# =========================================================
with flik_hem:
    h("""
    <div class="hero">
      <div class="badge">✨ Ny generation ekonomianalys</div>
      <h1>Förstå dina siffror.<br><span>Fatta bättre beslut.</span></h1>
      <p>Ladda upp era kvartalsrapporter, bygg en spårbar historik och följ omsättning, vinst och marginaler över tid – på ett ställe.</p>
      <p class="hint">→ Öppna fliken Analysverktyget för att komma igång</p>
    </div>
    <div class="stats">
      <div class="stat"><b>CSV · XLSX · PDF</b><span>Stödda filformat</span></div>
      <div class="stat"><b>10 MB</b><span>Max filstorlek</span></div>
      <div class="stat"><b>Per konto</b><span>Isolerad data för varje kund</span></div>
      <div class="stat"><b>Kvartalsvis</b><span>Tidsserier och marginaler</span></div>
    </div>
    """)

    h("""
    <div class="sec-head">
      <div class="eyebrow">Funktioner</div>
      <h2>Allt du behöver för att följa bolagets ekonomi</h2>
      <p>Från rapport till insikt – utan manuellt kalkylarksarbete.</p>
    </div>
    <div class="grid3">
      <div class="card"><div class="ico">⚡</div><h3>Snabb inläsning</h3><p>Ladda upp CSV, Excel eller PDF direkt. Filen kontrolleras för format och storlek innan analysen startar.</p></div>
      <div class="card"><div class="ico">🧮</div><h3>Automatiska nyckeltal</h3><p>Vinstmarginal beräknas och sparas för varje period, så att du alltid jämför samma mått.</p></div>
      <div class="card"><div class="ico">📈</div><h3>Tydliga tidsserier</h3><p>Följ omsättning, vinst och marginal kvartal för kvartal i interaktiva diagram.</p></div>
      <div class="card"><div class="ico">🔒</div><h3>Egen inloggning</h3><p>Varje kund loggar in med eget konto och ser enbart sin egen sparade data.</p></div>
      <div class="card"><div class="ico">🤖</div><h3>AI-sammanfattning</h3><p>Få en strukturerad sammanfattning med siffror, utveckling samt osäkerheter och risker att följa upp.</p></div>
      <div class="card"><div class="ico">📥</div><h3>Exportera historiken</h3><p>Ladda ner din samlade historik som CSV och använd den i era egna rapporter.</p></div>
    </div>
    """)

    h("""
    <div class="sec-head">
      <div class="eyebrow">Så fungerar det</div>
      <h2>Kom igång på tre steg</h2>
    </div>
    <div class="grid3">
      <div class="card"><div class="step-num">1</div><h3>Skapa ditt konto</h3><p>Registrera dig med e-post och lösenord och logga in i kundportalen.</p></div>
      <div class="card"><div class="step-num">2</div><h3>Ladda upp en rapport</h3><p>Välj fil och starta analysen för att få en första överblick.</p></div>
      <div class="card"><div class="step-num">3</div><h3>Spara och följ upp</h3><p>Spara nyckeltalen och bygg en historik som du kan följa över tid.</p></div>
    </div>
    """)

    h("""
    <div class="sec-head">
      <div class="eyebrow">Vanliga frågor</div>
      <h2>Frågor och svar</h2>
    </div>
    """)
    with st.expander("Vilka filformat stöds?"):
        st.write("CSV, XLSX och PDF, upp till 10 MB per fil.")
    with st.expander("Hur hanteras min data?"):
        st.write(
            "Din data sparas kopplad till ditt användarkonto och hämtas bara för den inloggade användaren. "
            "Använd ett starkt lösenord och dela aldrig dina inloggningsuppgifter."
        )
    with st.expander("Kan jag lita på AI-analysen?"):
        st.write(
            "AI-analysen är ett stöd och ersätter inte en granskning. Kontrollera alltid extraherade värden "
            "mot originalrapporten innan du fattar beslut."
        )
    with st.expander("Vad kostar tjänsten?"):
        st.write("Se fliken Priser för en översikt av planerna.")

# =========================================================
# PRISER
# =========================================================
with flik_priser:
    h("""
    <div class="sec-head" style="margin-top:34px;">
      <div class="eyebrow">Priser</div>
      <h2>Enkla medlemskap som växer med dig</h2>
      <p>Börja gratis och uppgradera när behovet ökar.</p>
    </div>
    <div class="grid3" style="margin-top:34px;">
      <div class="price"><h4>Freemium</h4><div class="amount">0 kr<small> /mån</small></div>
        <ul><li>3 analyser per månad</li><li>Filer upp till 5 MB</li><li>Manuell verifiering</li></ul></div>
      <div class="price pop"><div class="tag">MEST POPULÄR</div><h4>Growth Pro</h4><div class="amount">499 kr<small> /mån</small></div>
        <ul><li>Obegränsade analyser</li><li>Full molnhistorik</li><li>Automatiserade KPI-diagram</li></ul></div>
      <div class="price"><h4>Enterprise</h4><div class="amount">Offert</div>
        <ul><li>Egna AI-modeller</li><li>ERP-integrationer (t.ex. Fortnox)</li><li>Dedikerad support</li></ul></div>
    </div>
    """)

# =========================================================
# ANALYSVERKTYGET
# =========================================================
with flik_verktyg:
    if not st.session_state["user_authenticated"]:
        st.write("")
        _, mitt, _ = st.columns([1, 1.3, 1])
        with mitt:
            with st.container(border=True):
                h("""
                <div class="login-title">Välkommen</div>
                <div class="login-sub">Logga in eller skapa ett konto för att använda analysverktyget.</div>
                """)

                if not (supabase_url and supabase_key):
                    st.error("SUPABASE_URL och SUPABASE_ANON_KEY saknas i Secrets.")

                tab_in, tab_ny = st.tabs(["Logga in", "Skapa konto"])

                with tab_in:
                    with st.form("login_form"):
                        e_post = st.text_input("E-postadress", placeholder="namn@foretag.se")
                        losen = st.text_input("Lösenord", type="password")
                        skickat = st.form_submit_button("Logga in", type="primary")
                    if skickat:
                        if not (e_post and losen):
                            st.warning("Fyll i e-post och lösenord.")
                        elif not (supabase_url and supabase_key):
                            st.error("Databasen är inte konfigurerad.")
                        else:
                            try:
                                sb = initiera_supabase(supabase_url, supabase_key)
                                res = logga_in_anvandare(sb, e_post, losen)
                                if res["status"] == "Success":
                                    st.session_state["sb_client"] = sb
                                    st.session_state["user_authenticated"] = True
                                    st.session_state["user_email"] = e_post
                                    st.session_state["user_id"] = res["user_id"]
                                    st.rerun()
                                else:
                                    st.error(res["meddelande"])
                            except Exception as e:
                                st.error(f"Inloggningsfel: {str(e)}")

                with tab_ny:
                    with st.form("register_form"):
                        n_epost = st.text_input("E-postadress", placeholder="namn@foretag.se", key="reg_email")
                        n_losen = st.text_input("Lösenord (minst 6 tecken)", type="password", key="reg_pw")
                        n_losen2 = st.text_input("Upprepa lösenord", type="password", key="reg_pw2")
                        skapa = st.form_submit_button("Skapa konto", type="primary")
                    if skapa:
                        if not (n_epost and n_losen):
                            st.warning("Fyll i e-post och lösenord.")
                        elif n_losen != n_losen2:
                            st.error("Lösenorden matchar inte.")
                        elif not (supabase_url and supabase_key):
                            st.error("Databasen är inte konfigurerad.")
                        else:
                            try:
                                sb = initiera_supabase(supabase_url, supabase_key)
                                res = registrera_anvandare(sb, n_epost, n_losen)
                                if res["status"] == "Success":
                                    st.success("Konto skapat! Du kan nu logga in. Kontrollera din e-post om bekräftelse krävs.")
                                else:
                                    st.error(res["meddelande"])
                            except Exception as e:
                                st.error(f"Registreringsfel: {str(e)}")
    else:
        sb_client = st.session_state["sb_client"]

        kol_a, kol_b = st.columns([5, 1])
        with kol_a:
            h(f"""
            <div style="margin:22px 0 6px 0;">
              <div style="font-size:28px;font-weight:800;color:#0B1B3A;letter-spacing:-.6px;">Din ekonomiöversikt</div>
              <div style="font-size:15px;color:#64748B;">Inloggad som {st.session_state['user_email']}</div>
            </div>
            """)
        with kol_b:
            st.write("")
            if st.button("Logga ut"):
                if sb_client is not None:
                    logga_out_anvandare(sb_client)
                for k in ("user_authenticated", "user_email", "user_id", "sb_client"):
                    st.session_state[k] = False if k == "user_authenticated" else None
                st.rerun()

        if st.session_state["flash"]:
            st.success(st.session_state["flash"])
            st.session_state["flash"] = None

        db_data = pd.DataFrame()
        if sb_client is not None:
            db_data = hamta_historik_fran_supabase(sb_client, st.session_state["user_id"])

        t_over, t_analys, t_data = st.tabs(["📊 Översikt", "📄 Analysera rapport", "➕ Lägg till data"])

        # ---------------- Översikt ----------------
        with t_over:
            if db_data.empty:
                st.info("Ingen data sparad ännu. Gå till fliken Lägg till data för att spara dina första nyckeltal.")
            else:
                bolag = sorted(db_data["company_name"].dropna().unique())
                valt = bolag[0]
                if len(bolag) > 1:
                    valt = st.selectbox("Bolag", bolag)
                df = db_data[db_data["company_name"] == valt].sort_values(["year", "quarter"]).reset_index(drop=True)

                senaste = df.iloc[-1]
                forra = df.iloc[-2] if len(df) > 1 else None

                d_rev = procent_forandring(senaste["revenue"], forra["revenue"]) if forra is not None else None
                d_vinst = procent_forandring(senaste["profit"], forra["profit"]) if forra is not None else None
                d_marg = (senaste["profit_margin"] - forra["profit_margin"]) if forra is not None else None

                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Omsättning", kr(senaste["revenue"]), None if d_rev is None else f"{d_rev:+.1f}%")
                k2.metric("Vinst/Förlust", kr(senaste["profit"]), None if d_vinst is None else f"{d_vinst:+.1f}%")
                k3.metric("Vinstmarginal", f"{senaste['profit_margin']:.1f}%", None if d_marg is None else f"{d_marg:+.1f} p.e.")
                k4.metric("Sparade perioder", f"{len(df)}", f"Senast: {senaste['period']}", delta_color="off")

                st.write("")
                g1, g2 = st.columns(2)
                diagram = df.set_index("period")
                with g1:
                    st.markdown("**Omsättning och vinst**")
                    st.bar_chart(diagram[["revenue", "profit"]].rename(columns={"revenue": "Omsättning", "profit": "Vinst"}))
                with g2:
                    st.markdown("**Vinstmarginal (%)**")
                    st.line_chart(diagram[["profit_margin"]].rename(columns={"profit_margin": "Vinstmarginal %"}))

                visa = df[["company_name", "period", "revenue", "profit", "profit_margin"]].rename(columns={
                    "company_name": "Bolag",
                    "period": "Period",
                    "revenue": "Omsättning",
                    "profit": "Vinst",
                    "profit_margin": "Marginal %",
                })
                st.markdown("**Historik**")
                st.dataframe(visa, hide_index=True)
                st.download_button(
                    "Ladda ner som CSV",
                    visa.to_csv(index=False).encode("utf-8"),
                    file_name=f"{valt}_historik.csv",
                    mime="text/csv",
                )

        # ---------------- Analys ----------------
        with t_analys:
            st.write("")
            analys_nyckel = api_key
            if not analys_nyckel:
                analys_nyckel = st.text_input("OpenAI API-nyckel", type="password", key="main_openai_key")

            uploaded_file = st.file_uploader("Släpp din finansiella rapport här", type=["csv", "xlsx", "pdf"])

            if uploaded_file is not None and st.button("Starta analys", type="primary"):
                if analys_nyckel:
                    try:
                        report = parse_financial_file(uploaded_file.name, uploaded_file.getvalue())
                        st.session_state["analysis_output"] = analyze_report(report, analys_nyckel)
                        st.session_state["analysis_file"] = uploaded_file.name
                    except (FinancialFileError, ValueError) as e:
                        st.error(str(e))
                    except Exception as e:
                        st.error(f"Oväntat fel: {str(e)}")
                else:
                    st.warning("Ange en OpenAI API-nyckel först.")

            if "analysis_output" in st.session_state:
                st.markdown(f"#### Analysresultat: {st.session_state['analysis_file']}")
                with st.container(border=True):
                    st.markdown(st.session_state["analysis_output"])

        # ---------------- Lägg till data ----------------
        with t_data:
            st.write("")
            st.markdown("#### Spara nyckeltal för en period")
            with st.form("spara_finans_form", clear_on_submit=False):
                c1, c2, c3 = st.columns(3)
                bolagsnamn = c1.text_input("Bolagsnamn")
                aar = c2.number_input("År", min_value=1990, max_value=2100, value=2026, step=1)
                kvartal = c3.selectbox("Kvartal", ["Q1", "Q2", "Q3", "Q4"])
                c4, c5 = st.columns(2)
                omsattning = c4.number_input("Omsättning (kr)", min_value=0.0, value=0.0, step=1000.0)
                vinst = c5.number_input("Vinst/Förlust (kr)", value=0.0, step=1000.0)
                spara = st.form_submit_button("Spara period", type="primary")

            if spara:
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
                        st.session_state["flash"] = res["meddelande"]
                        st.rerun()
                    else:
                        st.error(res["meddelande"])

# =========================================================
# SIDFOT
# =========================================================
h("""
<div class="footer">
  <b>Finansanalytikern</b> · AI-driven ekonomianalys<br>
  © 2026 AI-Finansanalytikern AB · Informationen i tjänsten utgör inte finansiell rådgivning.
</div>
""")
